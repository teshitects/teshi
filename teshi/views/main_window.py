import os

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QMenuBar, QMenu, \
    QFrame, QPushButton, QDockWidget, QTextEdit, QToolBar, QTabWidget, QStatusBar, QProgressBar, QMessageBox, QToolButton
from PySide6.QtCore import Qt, QSize, QTimer, QFileInfo, Signal
from PySide6.QtGui import QAction, QIcon, QCloseEvent

from teshi.views.docks.markdown_highlighter import MarkdownHighlighter
from teshi.views.docks.project_explorer import ProjectExplorer
from teshi.views.docks.bdd_mind_map import BDDMindMapDock
from teshi.views.widgets.editor_widget import EditorWidget
from teshi.views.widgets.testcase_search_dialog import TestcaseSearchDialog
from teshi.utils.workspace_manager import WorkspaceManager
from teshi.utils.testcase_index_manager import TestCaseIndexManager
from teshi.utils.resource_path import resource_path


class MainWindow(QMainWindow):
    # Signal for global BDD mode changes
    global_bdd_mode_changed = Signal(bool)
    
    def __init__(self, project_name, project_path):
        super().__init__()
        self.project_name = project_name
        self.project_path = project_path
        self.setWindowTitle(f"{project_name} - Teshi - {project_path}")
        self.setWindowIcon(QIcon(resource_path("assets/teshi_icon64.png")))
        self.setGeometry(100, 100, 1200, 800)
        
        # Global BDD mode state
        self._global_bdd_mode = False
        
        # Flag to suppress updates during bulk operations (e.g., workspace restore)
        self._suppress_updates = False
        
        # Initialize workspace manager
        self.workspace_manager = WorkspaceManager(project_path, self)
        self.workspace_manager.set_main_window(self)
        
        # Initialize test case index manager
        self.index_manager = TestCaseIndexManager(project_path)
        
        # Timer for debouncing mind map updates
        self._mind_map_update_timer = QTimer()
        self._mind_map_update_timer.setSingleShot(True)
        self._mind_map_update_timer.setInterval(500)  # 500ms delay
        self._mind_map_update_timer.timeout.connect(self._do_update_mind_map)
        
        self._setup_menubar()
        self._setup_layout()
        self._setup_shortcuts()
        
        # Initialize test case index building in background
        QTimer.singleShot(100, self._initialize_testcase_index)
        
        # Restore workspace state
        self.workspace_manager.restore_workspace(self)



    def _setup_menubar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")
        import_action = QAction("Import Test Cases", self)
        file_menu.addAction(import_action)
        import_action.triggered.connect(self._import_test_cases)

        # Search Menu
        search_menu = menubar.addMenu("Search")
        search_testcase_action = QAction("Search Test Cases", self)
        search_menu.addAction(search_testcase_action)
        search_testcase_action.triggered.connect(self._show_testcase_search_dialog)
        
        rebuild_index_action = QAction("Rebuild Index", self)
        search_menu.addAction(rebuild_index_action)
        rebuild_index_action.triggered.connect(self._rebuild_testcase_index)

        # Help Menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        help_menu.addAction(about_action)
        about_action.triggered.connect(self._show_about_dialog)

    def _show_about_dialog(self):
        from teshi.views.widgets.about_dialog import AboutDialog
        about_dialog = AboutDialog()
        about_dialog.exec()

    def _initialize_testcase_index(self):
        """Initialize test case index in background"""
        try:
            if self.index_manager.is_first_open():
                self.show_message("Building test case index for the first time...")
            else:
                # Incremental update index
                self.show_message("Updating test case index...")
            
            # Start file watcher first
            self.index_manager.start_file_watcher()
            
            # Build index in background thread
            from PySide6.QtCore import QThread, Signal
            class IndexBuilderThread(QThread):
                finished = Signal(int)
                error = Signal(str)
                
                def __init__(self, index_manager):
                    super().__init__()
                    self.index_manager = index_manager
                
                def run(self):
                    try:
                        count = self.index_manager.build_index()
                        self.finished.emit(count)
                    except Exception as e:
                        self.error.emit(str(e))
            
            # Start background indexing
            self.index_thread = IndexBuilderThread(self.index_manager)
            self.index_thread.finished.connect(lambda count: self.show_message(f"Indexed {count} files", 3000))
            self.index_thread.error.connect(lambda error: self.show_message(f"Error building test case index: {error}", 5000))
            self.index_thread.start()
            
        except Exception as e:
            self.show_message(f"Error initializing test case index: {e}", 5000)

    def _show_testcase_search_dialog(self):
        """Show test case search dialog"""
        try:
            # Create dialog only if it doesn't exist or was closed
            if not hasattr(self, 'search_dialog') or not self.search_dialog.isVisible():
                self.search_dialog = TestcaseSearchDialog(self.index_manager, self)
            self.search_dialog.show()
            self.search_dialog.raise_()
            self.search_dialog.activateWindow()
        except Exception as e:
            self.show_message(f"Error opening search dialog: {e}", 5000)

    def _rebuild_testcase_index(self):
        """Rebuild test case index"""
        try:
            # Stop file watcher
            self.index_manager.stop_file_watcher()
            
            self.show_message("Rebuilding test case index...")
            count = self.index_manager.build_index(force_rebuild=True)
            self.show_message(f"Rebuilt index: {count} files processed", 3000)
            
            # Restart file watcher
            self.index_manager.start_file_watcher()
        except Exception as e:
            self.show_message(f"Error rebuilding test case index: {e}", 5000)

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

        # Left Toolbar
        left_toolbar = QToolBar("LeftToolbar", self)
        left_toolbar.setOrientation(Qt.Vertical)
        left_toolbar.setMovable(False)
        left_toolbar.setFloatable(False)
        left_toolbar.setFixedWidth(60)
        left_toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        left_toolbar.setIconSize(QSize(20, 20))
        left_toolbar.setStyleSheet("padding: 5")
        self.addToolBar(Qt.LeftToolBarArea, left_toolbar)

        action_project = left_toolbar.addAction(QIcon(resource_path("assets/icons/project.png")), "Project")
        action_project.triggered.connect(lambda: self.toggle_dock(self.project_dock))
        self.project_dock = QDockWidget("Project", self)
        self.explorer = ProjectExplorer(    self.project_path)
        self.project_dock.setWidget(self.explorer)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.project_dock)
        self.project_dock.hide()

        # Right Toolbar
        right_toolbar = QToolBar("RightToolbar", self)
        right_toolbar.setOrientation(Qt.Vertical)
        right_toolbar.setMovable(False)
        right_toolbar.setFloatable(False)
        right_toolbar.setFixedWidth(60)
        right_toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        right_toolbar.setIconSize(QSize(20, 20))
        right_toolbar.setStyleSheet("padding: 5")
        self.addToolBar(Qt.RightToolBarArea, right_toolbar)

        # Add BDD Mind Map dock to right toolbar
        action_bdd = right_toolbar.addAction(QIcon(resource_path("assets/icons/testcase_blue.png")), "BDD Mind Map")
        action_bdd.triggered.connect(lambda: self.toggle_dock(self.bdd_mind_map_dock))
        self.bdd_mind_map_dock = QDockWidget("BDD Mind Map", self)
        self.bdd_mind_map = BDDMindMapDock(self.project_path)
        self.bdd_mind_map_dock.setWidget(self.bdd_mind_map)
        self.addDockWidget(Qt.RightDockWidgetArea, self.bdd_mind_map_dock)
        self.bdd_mind_map_dock.hide()

        # central tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.setCentralWidget(self.tabs)
        self.tabs.tabCloseRequested.connect(self._close_tab_requested)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.explorer.file_open_requested.connect(self.open_file_in_tab)
        self.explorer.state_changed.connect(self.workspace_manager.trigger_save)

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
        
        # Search shortcut
        search_action = QAction("Search Test Cases", self)
        search_action.setShortcut(Qt.CTRL | Qt.SHIFT | Qt.Key_F)
        search_action.triggered.connect(self._show_testcase_search_dialog)
        self.addAction(search_action)

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

    def open_file_in_tab(self, path, suppress_updates=False):
        # check if already open
        for i in range(self.tabs.count()):
            if self.tabs.tabToolTip(i) == path:
                self.tabs.setCurrentIndex(i)
                return

        editor = EditorWidget(path)
        self.highlighter = MarkdownHighlighter(editor.text_edit.document())

        editor.modifiedChanged.connect(
            lambda dirty, ed=editor: self._update_tab_title_by_editor(ed, dirty)
        )
        
        # Connect editor content changes to mind map update (with debouncing)
        editor.text_edit.textChanged.connect(self._schedule_mind_map_update)
        
        # Connect to global BDD mode changes
        self.global_bdd_mode_changed.connect(editor.set_global_bdd_mode)
        
        # Apply current global BDD mode state
        editor.set_global_bdd_mode(self._global_bdd_mode)

        self.tabs.addTab(editor, os.path.basename(path))
        self.tabs.setTabToolTip(self.tabs.count() - 1, path)
        self.tabs.setCurrentWidget(editor)
        
        # Update mind map for newly opened file (only if not suppressed)
        if not suppress_updates and not self._suppress_updates:
            self._update_mind_map_for_current_file()
        
        # Trigger workspace save (only if not suppressed)
        if not suppress_updates and not self._suppress_updates:
            self.workspace_manager.trigger_save()

    def _update_tab_title_by_editor(self, editor: EditorWidget, dirty: bool):
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) is editor:
                base_name = os.path.basename(self.tabs.tabToolTip(i))
                title = f"{base_name}{' *' if dirty else ''}"
                self.tabs.setTabText(i, title)
                break
    
    def _on_tab_changed(self, index: int):
        """Handle tab change event"""
        # Activate pending BDD conversion if any
        current_widget = self.tabs.widget(index)
        if isinstance(current_widget, EditorWidget) and hasattr(current_widget, 'activate_if_pending'):
            current_widget.activate_if_pending()
        
        # Update mind map immediately when switching tabs (unless suppressed)
        if not self._suppress_updates:
            self._do_update_mind_map()
            # Trigger workspace save
            self.workspace_manager.trigger_save()
    
    def _schedule_mind_map_update(self):
        """Schedule a mind map update (with debouncing)"""
        # Skip if updates are suppressed
        if self._suppress_updates:
            return
        # Restart the timer - this effectively debounces rapid text changes
        self._mind_map_update_timer.stop()
        self._mind_map_update_timer.start()
    
    def _do_update_mind_map(self):
        """Actually update the mind map"""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, EditorWidget):
            file_path = current_widget.filePath
            # Get current content from editor
            content = current_widget.toPlainText()
            # Update mind map dock with current file content
            self.bdd_mind_map.load_bdd_from_content(file_path, content)
    
    def _update_mind_map_for_current_file(self):
        """Update BDD mind map with current file content (immediate)"""
        self._do_update_mind_map()

    def toggle_dock(self, dock):
        if dock.isVisible():
            dock.hide()
        else:
            dock.show()
        # Trigger workspace save
        self.workspace_manager.trigger_save()
    
    def _toggle_global_bdd_mode(self):
        """Toggle global BDD mode for all tabs"""
        self._global_bdd_mode = not self._global_bdd_mode
        
        # Emit signal to all editors
        self.global_bdd_mode_changed.emit(self._global_bdd_mode)
        
        # Apply BDD mode to all existing editor tabs
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget):
                widget.set_global_bdd_mode(self._global_bdd_mode)
        
        # Show message
        mode_text = "enabled" if self._global_bdd_mode else "disabled"
        self.show_message(f"Global BDD mode {mode_text}", 2000)
    
    def get_global_bdd_mode(self) -> bool:
        """Get current global BDD mode state"""
        return self._global_bdd_mode
    
    def closeEvent(self, event: QCloseEvent):
        """Window close event, save workspace state"""
        # Stop mind map update timer
        if hasattr(self, '_mind_map_update_timer'):
            self._mind_map_update_timer.stop()
        
        # Stop delayed save timer
        self.workspace_manager.save_timer.stop()
        
        # Stop file watcher (this may take up to 1 second)
        if hasattr(self, 'index_manager'):
            self.index_manager.stop_file_watcher()
        
        # Stop background index thread if still running
        if hasattr(self, 'index_thread') and self.index_thread.isRunning():
            self.index_thread.terminate()
            self.index_thread.wait(1000)  # Wait up to 1 second
        
        # Save workspace synchronously but optimized for fast shutdown
        try:
            self.workspace_manager.save_workspace(self)
            print("Workspace saved successfully")
        except Exception as e:
            print(f"Error saving workspace: {e}")
        
        event.accept()