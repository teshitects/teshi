"""
Git Dock Widget - Similar to VSCode/PyCharm Git panel
Shows Git status, staged/unstaged changes, and provides Git operations
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMenu, QMessageBox, QLineEdit,
    QTextEdit, QFrame, QSplitter, QToolButton, QComboBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QIcon

from teshi.services.git_service import GitService, GitFileStatus
from teshi.utils.resource_path import resource_path


class GitDock(QWidget):
    """Git dock widget for displaying Git status and operations"""

    file_open_requested = Signal(str)
    state_changed = Signal()

    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.git_service = GitService(project_path)

        self._setup_ui()
        self._connect_signals()

        # Initial status load
        self._refresh_status()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Header with branch info and refresh button
        header_layout = QHBoxLayout()

        # Branch display
        self.branch_label = QLabel("Branch: ")
        self.branch_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.branch_label)

        header_layout.addStretch()

        # Refresh button
        self.refresh_button = QToolButton()
        self.refresh_button.setText("Refresh")
        self.refresh_button.setStyleSheet("""
            QToolButton {
                padding: 4px 8px;
                border: 1px solid palette(mid);
                border-radius: 4px;
            }
            QToolButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        self.refresh_button.clicked.connect(self._refresh_status)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        # Commit message area
        commit_layout = QVBoxLayout()
        commit_label = QLabel("Commit Message:")
        commit_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        commit_layout.addWidget(commit_label)

        self.commit_input = QLineEdit()
        self.commit_input.setPlaceholderText("Enter commit message...")
        commit_layout.addWidget(self.commit_input)

        # Commit button
        commit_button_layout = QHBoxLayout()
        commit_button_layout.addStretch()

        self.commit_button = QPushButton("Commit")
        self.commit_button.setEnabled(False)
        self.commit_button.setStyleSheet("""
            QPushButton {
                padding: 6px 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: palette(mid);
                color: palette(mid);
            }
        """)
        self.commit_button.clicked.connect(self._commit_changes)
        commit_button_layout.addWidget(self.commit_button)

        commit_layout.addLayout(commit_button_layout)
        layout.addLayout(commit_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Changes section using splitter
        splitter = QSplitter(Qt.Vertical)

        # Staged changes
        staged_widget = self._create_changes_section("Staged Changes", "staged")
        self.staged_list = staged_widget.findChild(QListWidget, "staged_list")
        splitter.addWidget(staged_widget)

        # Unstaged changes
        unstaged_widget = self._create_changes_section("Unstaged Changes", "unstaged")
        self.unstaged_list = unstaged_widget.findChild(QListWidget, "unstaged_list")
        splitter.addWidget(unstaged_widget)

        # Untracked files
        untracked_widget = self._create_changes_section("Untracked Files", "untracked")
        self.untracked_list = untracked_widget.findChild(QListWidget, "untracked_list")
        splitter.addWidget(untracked_widget)

        # Set initial splitter sizes
        splitter.setSizes([100, 100, 100])
        layout.addWidget(splitter)

        # Bottom buttons for common operations
        bottom_layout = QHBoxLayout()

        self.stage_all_button = QPushButton("Stage All")
        self.stage_all_button.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid palette(mid);
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        self.stage_all_button.clicked.connect(self._stage_all)
        bottom_layout.addWidget(self.stage_all_button)

        self.pull_button = QPushButton("Pull")
        self.pull_button.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid palette(mid);
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        self.pull_button.clicked.connect(self._pull)
        bottom_layout.addWidget(self.pull_button)

        self.push_button = QPushButton("Push")
        self.push_button.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid palette(mid);
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        self.push_button.clicked.connect(self._push)
        bottom_layout.addWidget(self.push_button)

        bottom_layout.addStretch()

        layout.addLayout(bottom_layout)

        self.setLayout(layout)

        # Check if Git repo and show message if not
        if not self.git_service.is_git_repo():
            self._show_not_repo_message()

    def _create_changes_section(self, title: str, name: str) -> QWidget:
        """Create a section for displaying file changes"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)

        # Header with count
        header_layout = QHBoxLayout()

        label = QLabel(title)
        label.setStyleSheet("font-size: 11px; font-weight: bold;")
        header_layout.addWidget(label)

        count_label = QLabel(f"(0)")
        count_label.setStyleSheet("font-size: 10px; color: #666;")
        count_label.setObjectName(f"{name}_count")
        header_layout.addWidget(count_label)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # File list
        file_list = QListWidget()
        file_list.setObjectName(f"{name}_list")
        file_list.setMaximumHeight(150)
        file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        file_list.customContextMenuRequested.connect(
            lambda pos: self._show_file_context_menu(pos, name)
        )
        file_list.itemDoubleClicked.connect(
            lambda item: self._on_file_double_clicked(item, name)
        )
        layout.addWidget(file_list)

        widget.setLayout(layout)
        return widget

    def _connect_signals(self):
        """Connect Git service signals"""
        self.git_service.status_changed.connect(self._refresh_status)
        self.git_service.error_occurred.connect(self._on_error)
        self.git_service.operation_completed.connect(self._on_operation_completed)
        self.commit_input.textChanged.connect(self._on_commit_input_changed)

    def _refresh_status(self):
        """Refresh Git status display"""
        if not self.git_service.is_git_repo():
            return

        # Update branch
        branch = self.git_service.get_current_branch()
        self.branch_label.setText(f"Branch: {branch}")

        # Get file status
        staged, unstaged, untracked, conflicts = self.git_service.get_status()

        # Update lists
        self._update_file_list(self.staged_list, staged)
        self._update_file_list(self.unstaged_list, unstaged)
        self._update_file_list(self.untracked_list, untracked)

        # Update counts
        self.staged_list.parentWidget().findChild(QLabel, "staged_count").setText(f"({len(staged)})")
        self.unstaged_list.parentWidget().findChild(QLabel, "unstaged_count").setText(f"({len(unstaged)})")
        self.untracked_list.parentWidget().findChild(QLabel, "untracked_count").setText(f"({len(untracked)})")

        # Enable commit button if there are staged changes
        has_staged = len(staged) > 0
        self.commit_button.setEnabled(has_staged and bool(self.commit_input.text().strip()))

        # Check for conflicts
        if conflicts:
            self._show_conflicts_warning(conflicts)

    def _update_file_list(self, list_widget: QListWidget, files: list):
        """Update a file list with given files"""
        list_widget.clear()

        for file_status in files:
            item = QListWidgetItem()

            # Icon based on status
            icon_text = self._get_status_icon(file_status)
            item.setText(f"{icon_text} {file_status.path}")

            # Store file path in data
            item.setData(Qt.UserRole, file_status.path)

            # Tooltip
            item.setToolTip(f"{file_status.display_status}: {file_status.path}")

            list_widget.addItem(item)

    def _get_status_icon(self, file_status: GitFileStatus) -> str:
        """Get icon for file status"""
        # Using text-based icons for simplicity
        if file_status.is_conflicted:
            return "⚠"
        elif file_status.is_untracked:
            return "+"
        elif file_status.is_staged and file_status.is_unstaged:
            return "M"
        elif file_status.is_staged:
            match file_status.index_status:
                case "A":
                    return "A"
                case "D":
                    return "D"
                case "R":
                    return "R"
                case _:
                    return "S"
        elif file_status.is_unstaged:
            match file_status.work_status:
                case "D":
                    return "D"
                case _:
                    return "M"
        return "?"

    def _show_file_context_menu(self, position, list_type: str):
        """Show context menu for file in list"""
        list_widget = {
            "staged": self.staged_list,
            "unstaged": self.unstaged_list,
            "untracked": self.untracked_list
        }.get(list_type)

        if not list_widget:
            return

        item = list_widget.itemAt(position)
        if not item:
            return

        file_path = item.data(Qt.UserRole)
        menu = QMenu()

        if list_type == "staged":
            unstage_action = menu.addAction("Unstage")
            open_action = menu.addAction("Open File")
            discard_action = menu.addAction("Discard Changes")

            action = menu.exec_(list_widget.viewport().mapToGlobal(position))

            if action == unstage_action:
                self.git_service.unstage_file(file_path)
            elif action == open_action:
                self.file_open_requested.emit(file_path)
            elif action == discard_action:
                self._discard_changes(file_path)

        elif list_type == "unstaged":
            stage_action = menu.addAction("Stage")
            open_action = menu.addAction("Open File")
            discard_action = menu.addAction("Discard Changes")
            diff_action = menu.addAction("View Diff")

            action = menu.exec_(list_widget.viewport().mapToGlobal(position))

            if action == stage_action:
                self.git_service.stage_file(file_path)
            elif action == open_action:
                self.file_open_requested.emit(file_path)
            elif action == discard_action:
                self._discard_changes(file_path)
            elif action == diff_action:
                self._show_diff(file_path)

        elif list_type == "untracked":
            stage_action = menu.addAction("Stage")
            open_action = menu.addAction("Open File")
            delete_action = menu.addAction("Delete File")

            action = menu.exec_(list_widget.viewport().mapToGlobal(position))

            if action == stage_action:
                self.git_service.stage_file(file_path)
            elif action == open_action:
                self.file_open_requested.emit(file_path)
            elif action == delete_action:
                self._delete_file(file_path)

    def _on_file_double_clicked(self, item: QListWidgetItem, list_type: str):
        """Handle double click on file"""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self.file_open_requested.emit(file_path)

    def _commit_changes(self):
        """Commit staged changes"""
        message = self.commit_input.text().strip()
        if not message:
            QMessageBox.warning(self, "Commit", "Please enter a commit message.")
            return

        if self.git_service.commit(message):
            self.commit_input.clear()
            self._refresh_status()

    def _stage_all(self):
        """Stage all changes"""
        self.git_service.stage_all()

    def _pull(self):
        """Pull from remote"""
        # Get current branch
        branch = self.git_service.get_current_branch()
        if branch:
            self.git_service.pull(branch=branch)
        else:
            self.git_service.pull()

    def _push(self):
        """Push to remote"""
        # Get current branch
        branch = self.git_service.get_current_branch()
        if branch:
            self.git_service.push(branch=branch)
        else:
            self.git_service.push()

    def _discard_changes(self, file_path: str):
        """Discard changes to a file"""
        reply = QMessageBox.question(
            self,
            "Discard Changes",
            f"Are you sure you want to discard all changes to {os.path.basename(file_path)}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.git_service.discard_changes(file_path)

    def _delete_file(self, file_path: str):
        """Delete an untracked file"""
        reply = QMessageBox.question(
            self,
            "Delete File",
            f"Are you sure you want to delete {os.path.basename(file_path)}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                self._refresh_status()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete file: {e}")

    def _show_diff(self, file_path: str):
        """Show diff for a file"""
        diff = self.git_service.get_diff(file_path)
        if not diff:
            QMessageBox.information(self, "Diff", "No changes to show.")
            return

        # Create diff viewer dialog
        dialog = QMessageBox(self)
        dialog.setWindowTitle(f"Diff: {os.path.basename(file_path)}")
        dialog.setTextFormat(Qt.PlainText)
        dialog.setText(diff)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.setMinimumWidth(600)
        dialog.exec()

    def _show_conflicts_warning(self, conflicts: list):
        """Show warning about conflicted files"""
        files = "\n".join(f"  • {f.path}" for f in conflicts)
        QMessageBox.warning(
            self,
            "Merge Conflicts",
            f"The following files have merge conflicts:\n{files}\n\nPlease resolve conflicts before committing."
        )

    def _show_not_repo_message(self):
        """Show message when not in a Git repository"""
        self.staged_list.clear()
        self.unstaged_list.clear()
        self.untracked_list.clear()

        self.staged_list.addItem("Not a Git repository")
        self.branch_label.setText("Branch: N/A")
        self.commit_button.setEnabled(False)
        self.stage_all_button.setEnabled(False)
        self.pull_button.setEnabled(False)
        self.push_button.setEnabled(False)

    def _on_error(self, error_message: str):
        """Handle error from Git service"""
        QMessageBox.critical(self, "Git Error", error_message)

    def _on_operation_completed(self, operation: str, message: str):
        """Handle successful operation"""
        # Could show a toast notification here
        pass

    def _on_commit_input_changed(self):
        """Enable/disable commit button based on input"""
        has_staged = self.staged_list.count() > 0 and self.staged_list.item(0).text() != "Not a Git repository"
        self.commit_button.setEnabled(has_staged and bool(self.commit_input.text().strip()))

    def refresh(self):
        """Public method to refresh Git status"""
        self._refresh_status()

    def cleanup(self):
        """Clean up resources"""
        pass

    def __del__(self):
        """Destructor"""
        try:
            self.cleanup()
        except:
            pass
