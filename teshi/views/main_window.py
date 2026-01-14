import os

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QMenuBar, QMenu, \
    QFrame, QPushButton, QDockWidget, QTextEdit, QToolBar, QTabWidget, QStatusBar, QProgressBar, QMessageBox, QToolButton
from PySide6.QtCore import Qt, QSize, QTimer, QFileInfo, Signal
from PySide6.QtGui import QAction, QIcon, QCloseEvent

from teshi.views.docks.markdown_highlighter import MarkdownHighlighter
from teshi.views.docks.project_explorer import ProjectExplorer
from teshi.views.docks.bdd_mind_map import BDDMindMapDock
from teshi.views.docks.search_results import SearchResultsDock
from teshi.views.docks.ai_chat import AIChatDock
from teshi.views.widgets.editor_widget import EditorWidget
# from teshi.views.widgets.testcase_search_dialog import TestcaseSearchDialog  # No longer used
from teshi.utils.workspace_manager import WorkspaceManager
from teshi.utils.testcase_index_manager import TestCaseIndexManager
from teshi.utils.resource_path import resource_path


class MainWindow(QMainWindow):
    # Signal for global BDD mode changes
    global_bdd_mode_changed = Signal(bool)
    # Signal for global Automate mode changes
    global_automate_mode_changed = Signal(bool)
    
    def __init__(self, project_name, project_path):
        super().__init__()
        self.project_name = project_name
        self.project_path = project_path
        self.setWindowTitle(f"{project_name} - Teshi - {project_path}")
        self.setWindowIcon(QIcon(resource_path("assets/teshi_icon64.png")))
        self.setGeometry(100, 100, 1200, 800)
        
        # Global BDD mode state
        self._global_bdd_mode = False
        # Global Automate mode state
        self._global_automate_mode = False
        
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
        
        # Track last updated content to avoid unnecessary updates
        self._last_mind_map_content = None
        self._last_mind_map_file = None
        self._current_highlight_keywords = []  # Track current keywords for mind map updates
        
        # Debounce timer for search highlighting
        self._search_highlight_timer = QTimer()
        self._search_highlight_timer.setSingleShot(True)
        self._search_highlight_timer.setInterval(200)  # 200ms debounce
        self._search_highlight_timer.timeout.connect(self._apply_search_highlighting_debounced)
        self._pending_search_keywords = None
        
        # Flag to prevent infinite loop between mind map updates and text changes
        self._updating_mind_map = False
        
        self._setup_menubar()
        self._setup_layout()
        self._setup_shortcuts()
        
        # Initialize test case index building in background
        QTimer.singleShot(100, self._initialize_testcase_index)
        
        # Restore workspace state
        self.workspace_manager.restore_workspace(self)
        
        # Set default highlight color to yellow
        from PySide6.QtGui import QColor
        self.set_highlight_color(QColor(255, 255, 0))



    def _setup_menubar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")
        import_action = QAction("Import Test Cases", self)
        file_menu.addAction(import_action)
        import_action.triggered.connect(self._import_test_cases)
        
        # Add separator
        file_menu.addSeparator()
        
        # Close Project action
        close_project_action = QAction("Close Project", self)
        file_menu.addAction(close_project_action)
        close_project_action.triggered.connect(self._close_project)
        
        # Clear highlighting action
        clear_highlight_action = QAction("Clear Highlighting", self)
        # clear_highlight_action.setShortcut(Qt.CTRL | Qt.SHIFT | Qt.Key_H)
        # view_menu.addAction(clear_highlight_action)
        clear_highlight_action.triggered.connect(self.clear_highlight_keywords)

        # Help Menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        help_menu.addAction(about_action)
        about_action.triggered.connect(self._show_about_dialog)

        # Settings Menu
        settings_menu = menubar.addMenu("Settings")
        settings_action = QAction("Settings", self)
        settings_menu.addAction(settings_action)
        settings_action.triggered.connect(self._show_settings_dialog)

    def _show_about_dialog(self):
        from teshi.views.widgets.about_dialog import AboutDialog
        about_dialog = AboutDialog()
        about_dialog.exec()

    def _show_settings_dialog(self):
        """Show settings dialog"""
        from teshi.views.widgets.settings_dialog import SettingsDialog
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def apply_settings(self, settings):
        """Apply settings to the main window"""
        print(f"[MainWindow] Applying settings: {settings}")
        # Apply UI font size
        ui_font_size = settings.get('ui_font_size', 12)
        print(f"[MainWindow] Setting UI font size to: {ui_font_size}")
        font = self.font()
        font.setPointSize(ui_font_size)
        self.setFont(font)
        
        # Apply editor font size to all open tabs
        editor_font_size = settings.get('editor_font_size', 12)
        print(f"[MainWindow] Setting editor font size to: {editor_font_size}, open tabs: {self.tabs.count()}")
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget):
                editor_font = widget.text_edit.font()
                editor_font.setPointSize(editor_font_size)
                widget.text_edit.setFont(editor_font)
                print(f"[MainWindow] Applied editor font size to tab {i}")

    


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
        """Show test case search dialog (legacy method - no longer used)"""
        pass

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

    def _close_project(self):
        """Close the current project and return to project selection"""
        # Check if there are unsaved changes in any tab
        unsaved_tabs = []
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget) and widget.dirty:
                file_name = QFileInfo(widget.filePath).fileName()
                unsaved_tabs.append(file_name)
        
        if unsaved_tabs:
            # Show message about unsaved files
            unsaved_files = "\
".join(f"• {file}" for file in unsaved_tabs)
            answer = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"The following files have unsaved changes:\
\
{unsaved_files}\
\
"
                "Do you want to save them before closing the project?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save)
            
            if answer == QMessageBox.Cancel:
                return
            elif answer == QMessageBox.Save:
                # Save all modified files
                for i in range(self.tabs.count()):
                    widget = self.tabs.widget(i)
                    if isinstance(widget, EditorWidget) and widget.dirty:
                        if not widget.save():
                            # If save fails, cancel closing
                            return
        
        # Temporarily show docks to save their correct dimensions
        project_was_visible = self.project_dock.isVisible()
        search_was_visible = self.search_dock.isVisible()
        bdd_was_visible = self.bdd_mind_map_dock.isVisible()
        ai_chat_was_visible = self.ai_chat_dock.isVisible()
        
        # Save dock dimensions before cleanup
        if not project_was_visible:
            self.project_dock.show()
        if not search_was_visible:
            self.search_dock.show()
        if not bdd_was_visible:
            self.bdd_mind_map_dock.show()
        if not ai_chat_was_visible:
            self.ai_chat_dock.show()
        
        # Force update of the UI to ensure dimensions are correct
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Stop index manager
        try:
            self.index_manager.stop_file_watcher()
        except:
            pass  # Ignore errors during cleanup
        
        # Save workspace with correct dock dimensions
        self.workspace_manager.save_workspace(self)
        
        # Restore original visibility state before closing
        if not project_was_visible:
            self.project_dock.hide()
        if not search_was_visible:
            self.search_dock.hide()
        if not bdd_was_visible:
            self.bdd_mind_map_dock.hide()
        if not ai_chat_was_visible:
            self.ai_chat_dock.hide()
        
        # Close the main window and show project selection page
        from teshi.views.project_select_page import ProjectSelectPage
        
        # Create and show project selection page
        self.project_select_page = ProjectSelectPage()
        self.project_select_page.show()
        
        # Close the main window
        self.close()

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
        action_project.triggered.connect(lambda: self.switch_to_project_dock())
        self.project_dock = QDockWidget("Project", self)
        self.explorer = ProjectExplorer(self.project_path)
        self.project_dock.setWidget(self.explorer)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.project_dock)
        self.project_dock.hide()
        
        # Add search action to left toolbar (below project button)
        action_search = left_toolbar.addAction(QIcon(resource_path("assets/icons/search.png")), "Search")
        action_search.triggered.connect(lambda: self.switch_to_search_dock())
        self.search_dock = QDockWidget("Search", self)
        self.search_results = SearchResultsDock(self.index_manager)
        self.search_results.file_open_requested.connect(self.open_file_in_tab)
        self.search_results.state_changed.connect(self.workspace_manager.trigger_save)
        # Connect search text changes to keyword highlighting
        self.search_results.search_edit.textChanged.connect(self._on_search_text_changed)
        self.search_dock.setWidget(self.search_results)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.search_dock)
        self.search_dock.hide()
        
        # Track which dock is currently visible in the left area
        self.current_left_dock = None  # None, 'project', or 'search'

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
        action_bdd = right_toolbar.addAction(QIcon(resource_path("assets/icons/mindmap.png")), "BDD Mind Map")
        action_bdd.triggered.connect(lambda: self.toggle_dock(self.bdd_mind_map_dock))
        self.bdd_mind_map_dock = QDockWidget("BDD Mind Map", self)
        self.bdd_mind_map = BDDMindMapDock(self.project_path)
        # Set default highlight color to yellow for mind map
        from PySide6.QtGui import QColor
        self.bdd_mind_map.set_highlight_color(QColor(255, 255, 0))  # Yellow background
        self.bdd_mind_map_dock.setWidget(self.bdd_mind_map)
        self.addDockWidget(Qt.RightDockWidgetArea, self.bdd_mind_map_dock)
        self.bdd_mind_map_dock.hide()

        # Add AI Chat dock to right toolbar
        action_ai = right_toolbar.addAction("AI Chat")
        action_ai.triggered.connect(lambda: self.toggle_dock(self.ai_chat_dock))
        self.ai_chat_dock = QDockWidget("AI Chat", self)
        self.ai_chat = AIChatDock(self)
        self.ai_chat_dock.setWidget(self.ai_chat)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_chat_dock)
        self.ai_chat_dock.hide()

        # central tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.setCentralWidget(self.tabs)
        self.tabs.tabCloseRequested.connect(self._close_tab_requested)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        # Enable context menu on tabs
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self._show_tab_context_menu)
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
        
        # Clean up resources properly
        if isinstance(widget, EditorWidget):
            # Disconnect signals to prevent memory leaks
            if hasattr(widget, '_signal_connections'):
                for signal, slot in widget._signal_connections:
                    try:
                        signal.disconnect(slot)
                    except:
                        pass
                widget._signal_connections.clear()
            
            # Clean up highlighter
            if hasattr(widget, 'highlighter'):
                widget.highlighter.setDocument(None)
                widget.highlighter.deleteLater()
                widget.highlighter = None
            
            # Clean up editor's own timer
            if hasattr(widget, '_highlight_timer'):
                widget._highlight_timer.stop()
                widget._highlight_timer.deleteLater()
                delattr(widget, '_highlight_timer')
        
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
                # Only switch to the tab if not suppressing updates
                if not suppress_updates and not self._suppress_updates:
                    self.tabs.setCurrentIndex(i)
                    # Apply current search highlighting when switching to existing tab
                    self._apply_current_search_highlighting()
                return

        editor = EditorWidget(path)
        # Store highlighter reference in editor widget for proper cleanup
        from teshi.views.docks.markdown_highlighter import MarkdownHighlighter
        editor.highlighter = MarkdownHighlighter(editor.text_edit.document())

        # Store slot function for proper disconnection later
        slot_update_title = lambda dirty, ed=editor: self._update_tab_title_by_editor(ed, dirty)
        editor.modifiedChanged.connect(slot_update_title)
        
        # Connect editor content changes to mind map update (with debouncing)
        editor.text_edit.textChanged.connect(self._schedule_mind_map_update)
        
        # Connect to global BDD mode changes
        self.global_bdd_mode_changed.connect(editor.set_global_bdd_mode)
        
        # Connect to global Automate mode changes
        if hasattr(editor, 'set_global_automate_mode'):
            self.global_automate_mode_changed.connect(editor.set_global_automate_mode)
        
        # Store signal connections for cleanup
        editor._signal_connections = [
            (editor.modifiedChanged, slot_update_title),
            (editor.text_edit.textChanged, self._schedule_mind_map_update),
            (self.global_bdd_mode_changed, editor.set_global_bdd_mode)
        ]
        if hasattr(editor, 'set_global_automate_mode'):
            editor._signal_connections.append((self.global_automate_mode_changed, editor.set_global_automate_mode))
        
        # Set default highlight color to yellow
        from PySide6.QtGui import QColor
        editor.set_highlight_color(QColor(255, 255, 0))  # Yellow background
        
        # Apply current global BDD mode state (with deferred conversion if suppressing updates)
        if suppress_updates or self._suppress_updates:
            editor.set_global_bdd_mode(self._global_bdd_mode, defer_conversion=True)
            if hasattr(editor, 'set_global_automate_mode'):
                editor.set_global_automate_mode(self._global_automate_mode, defer_conversion=True)
        else:
            editor.set_global_bdd_mode(self._global_bdd_mode)
            if hasattr(editor, 'set_global_automate_mode'):
                editor.set_global_automate_mode(self._global_automate_mode)

        self.tabs.addTab(editor, os.path.basename(path))
        self.tabs.setTabToolTip(self.tabs.count() - 1, path)
        
        # Only set as current widget if not suppressing updates
        if not suppress_updates and not self._suppress_updates:
            self.tabs.setCurrentWidget(editor)
            # Apply current search highlighting to newly opened tab
            self._apply_current_search_highlighting()
        
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
        print(f"[MAIN] Tab changed to index {index}")
        # Activate pending BDD conversion if any
        current_widget = self.tabs.widget(index)
        if isinstance(current_widget, EditorWidget) and hasattr(current_widget, 'activate_if_pending'):
            current_widget.activate_if_pending()
        
        # Update mind map immediately when switching tabs (unless suppressed)
        if not self._suppress_updates:
            # Clear content tracking to force update on tab change
            self._last_mind_map_file = None
            self._last_mind_map_content = None
            self._do_update_mind_map()
            # Trigger workspace save
            self.workspace_manager.trigger_save()
    
    def _show_tab_context_menu(self, position):
        """Show context menu for tabs"""
        # Get the tab at the click position
        tab_bar = self.tabs.tabBar()
        tab_index = tab_bar.tabAt(position)
        
        if tab_index == -1:
            return  # Click was not on a tab
        
        self._context_tab_index = tab_index
        
        # Create context menu
        menu = QMenu(self)
        
        # Close action
        close_action = menu.addAction("Close")
        close_action.triggered.connect(self._close_context_tab)
        
        # Close Other Tabs action
        close_others_action = menu.addAction("Close Other Tabs")
        close_others_action.triggered.connect(self._close_other_tabs)
        
        # Close All Tabs action
        close_all_action = menu.addAction("Close All Tabs")
        close_all_action.triggered.connect(self._close_all_tabs)
        
        # Show menu
        menu.exec_(tab_bar.mapToGlobal(position))
    
    def _close_context_tab(self):
        """Close the tab that was right-clicked"""
        if hasattr(self, '_context_tab_index'):
            self._close_tab_requested(self._context_tab_index)
    
    def _close_other_tabs(self):
        """Close all tabs except the one that was right-clicked"""
        if not hasattr(self, '_context_tab_index'):
            return
        
        # Get the tab to keep
        keep_index = self._context_tab_index
        
        # Close all other tabs
        # We need to close from highest index to lowest to avoid index changes
        for i in range(self.tabs.count() - 1, -1, -1):
            if i != keep_index:
                self._close_tab_requested(i)
    
    def _close_all_tabs(self):
        """Close all tabs"""
        # Close all tabs from highest index to lowest
        for i in range(self.tabs.count() - 1, -1, -1):
            self._close_tab_requested(i)
    
    def _schedule_mind_map_update(self):
        """Schedule a mind map update (with debouncing)"""
        # Skip if updates are suppressed or if we're already updating mind map
        if self._suppress_updates or self._updating_mind_map:
            return
        print("[MINDMAP] _schedule_mind_map_update called")
        # Restart the timer - this effectively debounces rapid text changes
        self._mind_map_update_timer.stop()
        self._mind_map_update_timer.start()
    
    def _do_update_mind_map(self):
        """Actually update the mind map"""
        print("[MINDMAP] _do_update_mind_map executed")
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, EditorWidget) and hasattr(self, 'bdd_mind_map') and self.bdd_mind_map:
            file_path = current_widget.filePath
            # Get current content from editor
            content = current_widget.toPlainText()
            
            # Only update if content or file has changed
            if (file_path != self._last_mind_map_file or 
                content != self._last_mind_map_content):
                
                self._last_mind_map_file = file_path
                self._last_mind_map_content = content
                
                print(f"[MINDMAP] Updating mind map for file: {file_path}")
                
                # Set flag to prevent infinite loop
                self._updating_mind_map = True
                
                try:
                    # Update mind map dock with current file content
                    self.bdd_mind_map.load_bdd_from_content(file_path, content)
                    
                    # Only apply highlighting to current widget to avoid affecting other tabs
                    if hasattr(self, '_current_highlight_keywords') and self._current_highlight_keywords:
                        print(f"[MINDMAP] Applying highlighting to current tab only: {self._current_highlight_keywords}")
                        current_widget.set_highlight_keywords(self._current_highlight_keywords)
                    else:
                        print(f"[MINDMAP] No keywords to highlight for current tab")
                        
                finally:
                    # Always clear the flag, even if there's an error
                    self._updating_mind_map = False
                    print(f"[MINDMAP] Mind map update completed for {file_path}")
        else:
            print("[MINDMAP] Skipping mind map update - no changes")
    
    def _update_mind_map_for_current_file(self):
        """Update BDD mind map with current file content (immediate)"""
        self._do_update_mind_map()

    def switch_to_project_dock(self):
        """Switch to project explorer dock"""
        if self.current_left_dock == 'project':
            # If project is already visible, hide it
            self.project_dock.hide()
            self.current_left_dock = None
        else:
            # Hide search dock if visible
            if self.search_dock.isVisible():
                self.search_dock.hide()
            # Show project dock
            self.project_dock.show()
            self.current_left_dock = 'project'
        # Trigger workspace save
        self.workspace_manager.trigger_save()
        
    def switch_to_search_dock(self):
        """Switch to search results dock"""
        if self.current_left_dock == 'search':
            # If search is already visible, hide it
            self.search_dock.hide()
            self.current_left_dock = None
        else:
            # Hide project dock if visible
            if self.project_dock.isVisible():
                self.project_dock.hide()
            # Show search dock
            self.search_dock.show()
            self.current_left_dock = 'search'
        # Trigger workspace save
        self.workspace_manager.trigger_save()
    
    def toggle_dock(self, dock):
        """Legacy toggle method for backward compatibility"""
        if dock.isVisible():
            dock.hide()
        else:
            dock.show()
        # Trigger workspace save
        self.workspace_manager.trigger_save()
    
    def _toggle_global_bdd_mode(self):
        """Toggle global BDD mode for all tabs"""
        self._global_bdd_mode = not self._global_bdd_mode
        
        # If enabling BDD mode, disable Automate mode (mutually exclusive)
        if self._global_bdd_mode and self._global_automate_mode:
            self._global_automate_mode = False
            self.global_automate_mode_changed.emit(False)
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if isinstance(widget, EditorWidget) and hasattr(widget, 'set_global_automate_mode'):
                    widget.set_global_automate_mode(False)
        
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

    def _toggle_global_automate_mode(self):
        """Toggle global Automate mode for all tabs"""
        self._global_automate_mode = not self._global_automate_mode
        
        # If enabling Automate mode, disable BDD mode (mutually exclusive)
        if self._global_automate_mode and self._global_bdd_mode:
            self._global_bdd_mode = False
            self.global_bdd_mode_changed.emit(False)
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if isinstance(widget, EditorWidget):
                    widget.set_global_bdd_mode(False)
        
        # Emit signal to all editors
        self.global_automate_mode_changed.emit(self._global_automate_mode)
        
        # Apply Automate mode to all existing editor tabs
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget) and hasattr(widget, 'set_global_automate_mode'):
                widget.set_global_automate_mode(self._global_automate_mode)
        
        # Show message
        mode_text = "enabled" if self._global_automate_mode else "disabled"
        self.show_message(f"Global Automate mode {mode_text}", 2000)
    
    def get_global_bdd_mode(self) -> bool:
        """Get current global BDD mode state"""
        return self._global_bdd_mode
    
    def closeEvent(self, event: QCloseEvent):
        """Window close event, save workspace state"""
        # Stop mind map update timer
        if hasattr(self, '_mind_map_update_timer'):
            self._mind_map_update_timer.stop()
            self._mind_map_update_timer.deleteLater()
        
        # Stop search highlight timer
        if hasattr(self, '_search_highlight_timer'):
            self._search_highlight_timer.stop()
            self._search_highlight_timer.deleteLater()
        
        # Stop delayed save timer
        self.workspace_manager.save_timer.stop()
        
        # Stop file watcher (this may take up to 1 second)
        if hasattr(self, 'index_manager'):
            self.index_manager.cleanup()
        
        # Stop background index thread if still running
        if hasattr(self, 'index_thread') and self.index_thread.isRunning():
            self.index_thread.terminate()
            self.index_thread.wait(1000)  # Wait up to 1 second
        
        # Disconnect all signals to prevent memory leaks
        try:
            # Disconnect tab widget signals
            self.tabs.tabCloseRequested.disconnect()
            self.tabs.currentChanged.disconnect()
            
            # Disconnect editor signals if any
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if hasattr(widget, 'textChanged'):
                    try:
                        widget.textChanged.disconnect()
                    except:
                        pass
                if hasattr(widget, '_highlight_timer'):
                    widget._highlight_timer.stop()
                    widget._highlight_timer.deleteLater()
            
            # Disconnect search results signals and cleanup
            if hasattr(self, 'search_results'):
                try:
                    self.search_results.file_selected.disconnect()
                    self.search_results.cleanup()
                except:
                    pass
            
            print("Signals disconnected successfully")
        except Exception as e:
            print(f"Error disconnecting signals: {e}")
        
        # Save workspace synchronously but optimized for fast shutdown
        try:
            self.workspace_manager.save_workspace(self)
            print("Workspace saved successfully")
        except Exception as e:
            print(f"Error saving workspace: {e}")
        
        event.accept()
    
    def _set_highlight_keywords_current_tab(self, keywords: list):
        """设置当前活动编辑器标签页的关键字高亮"""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, EditorWidget):
            self._current_highlight_keywords = keywords
            current_widget.set_highlight_keywords(keywords)
    
    def _clear_highlight_keywords_current_tab(self):
        """清除当前活动编辑器标签页的关键字高亮"""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, EditorWidget):
            current_widget.clear_highlight_keywords()
    
    def _apply_current_search_highlighting(self):
        """应用当前搜索框的关键字高亮到当前tab"""
        search_text = self.search_results.search_edit.text().strip()
        
        if search_text:
            # If there is search text, split keywords by space and comma
            import re
            # Use regex to split keywords, supporting space and comma separation
            keywords = re.split(r'[,，\s]+', search_text)
            # Filter empty strings
            keywords = [kw.strip() for kw in keywords if kw.strip()]
            
            if keywords:
                # Set default yellow highlight
                from PySide6.QtGui import QColor
                current_widget = self.tabs.currentWidget()
                if isinstance(current_widget, EditorWidget):
                    current_widget.set_highlight_color(QColor(255, 255, 0))
                    current_widget.set_highlight_keywords(keywords)
    
    # Keyword highlighting methods for all editor tabs
    def set_highlight_keywords(self, keywords: list):
        """设置所有打开的编辑器标签页的关键字高亮"""
        self._current_highlight_keywords = keywords
        # Apply to all editor tabs
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget):
                widget.set_highlight_keywords(keywords)
        
        # Apply to BDD mind map
        if hasattr(self, 'bdd_mind_map'):
            self.bdd_mind_map.set_highlight_keywords(keywords)
    
    def add_highlight_keyword(self, keyword: str):
        """为所有编辑器添加单个关键字高亮"""
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget):
                widget.add_highlight_keyword(keyword)
        
        # Apply to BDD mind map
        if hasattr(self, 'bdd_mind_map'):
            self.bdd_mind_map.add_highlight_keyword(keyword)
    
    def remove_highlight_keyword(self, keyword: str):
        """从所有编辑器移除关键字高亮"""
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget):
                widget.remove_highlight_keyword(keyword)
        
        # Apply to BDD mind map
        if hasattr(self, 'bdd_mind_map'):
            self.bdd_mind_map.remove_highlight_keyword(keyword)
    
    def clear_highlight_keywords(self):
        """清除所有编辑器的关键字高亮"""
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget):
                widget.clear_highlight_keywords()
        
        # Apply to BDD mind map
        if hasattr(self, 'bdd_mind_map'):
            self.bdd_mind_map.clear_highlight_keywords()
    
    def set_highlight_color(self, color):
        """"""
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget):
                widget.set_highlight_color(color)
        
        # Apply to BDD mind map
        if hasattr(self, 'bdd_mind_map'):
            self.bdd_mind_map.set_highlight_color(color)
    
    def _on_search_text_changed(self):
        """Handle search text changes with debouncing"""
        from PySide6.QtGui import QColor
        search_text = self.search_results.search_edit.text().strip()
        
        # Store pending keywords and restart debounce timer
        if search_text:
            import re
            # Use regex to split keywords, supporting space and comma separation
            keywords = re.split(r'[,，\s]+', search_text)
            # Filter empty strings
            keywords = [kw.strip() for kw in keywords if kw.strip()]
            self._pending_search_keywords = keywords if keywords else None
        else:
            self._pending_search_keywords = None
        
        # Restart debounce timer
        self._search_highlight_timer.stop()
        self._search_highlight_timer.start()
    
    def _apply_search_highlighting_debounced(self):
        """Apply search highlighting after debounce"""
        from PySide6.QtGui import QColor
        
        print(f"[SEARCH] _apply_search_highlighting_debounced with keywords: {self._pending_search_keywords}")
        keywords = self._pending_search_keywords
        
        if keywords:
            # Set default yellow highlight
            self.set_highlight_color(QColor(255, 255, 0))
            # Apply keyword highlighting only to current tab
            self._set_highlight_keywords_current_tab(keywords)
            # Also apply to BDD mind map (with error handling)
            if hasattr(self, 'bdd_mind_map') and self.bdd_mind_map:
                try:
                    self.bdd_mind_map.set_highlight_keywords(keywords)
                except RuntimeError as e:
                    if "already deleted" in str(e):
                        print("BDD mind map object deleted, skipping highlight")
                    return
                except Exception as e:
                    print(f"Error applying BDD mind map highlight: {e}")
                    return
            self.show_message(f"Highlighting keywords: {', '.join(keywords)}", 2000)
        else:
            # Clear highlighting
            self._clear_highlight_keywords_current_tab()
            if hasattr(self, 'bdd_mind_map') and self.bdd_mind_map:
                try:
                    self.bdd_mind_map.clear_highlight_keywords()
                except RuntimeError as e:
                    if "already deleted" in str(e):
                        print("BDD mind map object deleted, skipping clear")
                    return
                except Exception as e:
                    print(f"Error clearing BDD mind map highlight: {e}")
                    return
    
    def get_highlight_keywords(self) -> list:
        """Get current keyword list (from the first editor)"""
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorWidget):
                return widget.get_highlight_keywords()
        return []