import os

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QMenuBar, QMenu, \
    QFrame, QPushButton, QDockWidget, QTextEdit, QToolBar, QTabWidget, QStatusBar, QProgressBar, QMessageBox
from PySide6.QtCore import Qt, QSize, QTimer, QFileInfo
from PySide6.QtGui import QAction, QIcon, QCloseEvent

from teshi.views.docks.markdown_highlighter import MarkdownHighlighter
from teshi.views.docks.project_explorer import ProjectExplorer
from teshi.views.widgets.editor_widget import EditorWidget
from teshi.utils.workspace_manager import WorkspaceManager


class MainWindow(QMainWindow):
    def __init__(self, project_name, project_path):
        super().__init__()
        self.project_name = project_name
        self.project_path = project_path
        self.setWindowTitle(f"{project_name} - Teshi - {project_path}")
        self.setWindowIcon(QIcon("assets/teshi_icon64.png"))
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize workspace manager
        self.workspace_manager = WorkspaceManager(project_path, self)
        self.workspace_manager.set_main_window(self)
        
        self._setup_menubar()
        self._setup_layout()
        self._setup_shortcuts()
        
        # Restore workspace state
        self.workspace_manager.restore_workspace(self)



    def _setup_menubar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")
        import_action = QAction("Import Test Cases", self)
        file_menu.addAction(import_action)
        import_action.triggered.connect(self._import_test_cases)

        # Help Menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        help_menu.addAction(about_action)
        about_action.triggered.connect(self._show_about_dialog)

    def _show_about_dialog(self):
        from teshi.views.widgets.about_dialog import AboutDialog
        about_dialog = AboutDialog()
        about_dialog.exec()

    def _import_test_cases(self):
        from PySide6.QtWidgets import QFileDialog
        # file_path, _ = QFileDialog.getOpenFileName(self, "Open Test Case File", "", "JSON Files (*.json);;All Files (*)")

        # from teshi.views.widgets.import_testcase_wizard_dialog import TestcaseImportDialog
        # import_dialog = TestcaseImportDialog(self)
        # import_dialog.exec()

    def _setup_layout(self):
        # Main Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout(main_widget)

        toolbar = QToolBar("LeftToolbar", self)
        toolbar.setOrientation(Qt.Vertical)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setFixedWidth(60)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setStyleSheet("padding: 5")
        self.addToolBar(Qt.LeftToolBarArea, toolbar)

        action_project = toolbar.addAction(QIcon("assets/icons/project.png"), "Project")
        action_project.triggered.connect(lambda: self.toggle_dock(self.project_dock))
        self.project_dock = QDockWidget("Project", self)
        self.explorer = ProjectExplorer(    self.project_path)
        self.project_dock.setWidget(self.explorer)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.project_dock)
        self.project_dock.hide()

        # central tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.setCentralWidget(self.tabs)
        self.tabs.tabCloseRequested.connect(self._close_tab_requested)
        self.tabs.currentChanged.connect(lambda: self.workspace_manager.trigger_save())
        self.explorer.file_open_requested.connect(self.open_file_in_tab)

        # status bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.msg_label = QLabel()
        self.msg_label.setObjectName("msgLabel")
        self.msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        status_bar.addWidget(self.msg_label, 1)

        self.progress = QProgressBar()
        self.progress.setMaximumWidth(150)
        self.progress.setMaximumHeight(12)
        self.progress.setVisible(False)
        self.progress.setObjectName("statusProgress")
        status_bar.addPermanentWidget(self.progress)
        self.show_message("Ready")

    def _setup_shortcuts(self):
        save_action = QAction(QIcon.fromTheme("document-save"), "Save", self)
        save_action.setShortcut(Qt.CTRL | Qt.Key_S)
        save_action.triggered.connect(self._save_current_editor)
        self.addAction(save_action)

    def _save_current_editor(self):
        current = self.tabs.currentWidget()
        if isinstance(current, EditorWidget):
            if current.save():
                self.show_message("File saved.", 2000)
                # Trigger workspace save
                self.workspace_manager.trigger_save()
            else:
                self.show_message("Save failed.", 4000)
        else:
            self.show_message("No editor to save.", 2000)

    def _close_tab_requested(self, index):
        widget = self.tabs.widget(index)
        if isinstance(widget, EditorWidget) and widget.dirty:
            answer = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"The file <b>{QFileInfo(widget.filePath).fileName()}</b> has been modified.\n"
                "Do you want to save it before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save)
            if answer == QMessageBox.Save:
                if not widget.save():
                    return
            elif answer == QMessageBox.Cancel:
                return
        self.tabs.removeTab(index)
        widget.deleteLater()
        
        # Trigger workspace save
        self.workspace_manager.trigger_save()

    def show_message(self, text: str, timeout: int = 0):
        self.msg_label.setText(text)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.msg_label.setText(""))

    def open_file_in_tab(self, path):
        # check if already open
        for i in range(self.tabs.count()):
            if self.tabs.tabToolTip(i) == path:
                self.tabs.setCurrentIndex(i)
                return

        editor = EditorWidget(path)
        self.highlighter = MarkdownHighlighter(editor.document())

        editor.modifiedChanged.connect(
            lambda dirty, ed=editor: self._update_tab_title_by_editor(ed, dirty)
        )

        self.tabs.addTab(editor, os.path.basename(path))
        self.tabs.setTabToolTip(self.tabs.count() - 1, path)
        self.tabs.setCurrentWidget(editor)
        
        # Trigger workspace save
        self.workspace_manager.trigger_save()

    def _update_tab_title_by_editor(self, editor: EditorWidget, dirty: bool):
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) is editor:
                base_name = os.path.basename(self.tabs.tabToolTip(i))
                title = f"{base_name}{' *' if dirty else ''}"
                self.tabs.setTabText(i, title)
                break

    def toggle_dock(self, dock):
        if dock.isVisible():
            dock.hide()
        else:
            dock.show()
        # Trigger workspace save
        self.workspace_manager.trigger_save()
    
    def closeEvent(self, event: QCloseEvent):
        """Window close event, save workspace state"""
        # Stop delayed save timer
        self.workspace_manager.save_timer.stop()
        # Save workspace immediately
        self.workspace_manager.save_workspace(self)
        event.accept()