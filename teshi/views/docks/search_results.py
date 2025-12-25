import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QTreeView, QMenu, QMessageBox, QLabel, QFrame, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon

from teshi.utils.testcase_index_manager import TestCaseIndexManager
from teshi.utils.resource_path import resource_path
from teshi.utils.tree_utils import TreeBuilder


class SearchResultsDock(QWidget):
    """Search results dock widget"""
    
    file_open_requested = Signal(str)
    state_changed = Signal()
    
    def __init__(self, index_manager: TestCaseIndexManager, parent=None):
        super().__init__(parent)
        self.index_manager = index_manager
        self.current_results = []
        self.tree_builder = TreeBuilder()
        # Use the same project_path as the index manager (same as Project Explorer)
        self.project_path = index_manager.project_path
        
        # Debounce timer for search
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(300)  # 300ms debounce
        self.debounce_timer.timeout.connect(self._perform_search)
        
        # Store last search query to maintain results when cleared
        self.last_search_query = ""
        
        self._setup_ui()
        self._load_statistics()
        
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Search area
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter search terms...")
        # Connect text change event for debounce search
        self.search_edit.textChanged.connect(self._on_text_changed)
        
        search_layout.addWidget(self.search_edit, 1)
        layout.addLayout(search_layout)
        
        # Statistics information
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 11px; padding: 2px;")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Results tree
        self.results_tree = QTreeView()
        self.results_tree.setHeaderHidden(True)
        self.results_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_tree.customContextMenuRequested.connect(self._open_context_menu)
        self.results_tree.doubleClicked.connect(self._on_double_click)
        
        # Setup model
        self.results_model = QStandardItemModel()
        self.results_tree.setModel(self.results_model)
        
        # Expand tree
        self.results_tree.setExpandsOnDoubleClick(True)
        
        layout.addWidget(self.results_tree)
        
        # Bottom button area
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)
        
        # Add stretch to push button to the right
        button_layout.addStretch()
        
        # Rebuild Index button
        self.rebuild_button = QPushButton("Rebuild Index")
        self.rebuild_button.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-radius: 4px;
                font-size: 12px;
                color: palette(button-text);
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                border: 1px solid palette(highlight);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
            QPushButton:disabled {
                background-color: palette(midlight);
                color: palette(mid);
                border: 1px solid palette(midlight);
            }
        """)
        self.rebuild_button.clicked.connect(self._rebuild_index)
        button_layout.addWidget(self.rebuild_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Icons
        self.result_icon = QIcon(resource_path("assets/icons/testcase_blue.png"))
        
    def _load_statistics(self):
        """Load statistics information"""
        stats = self.index_manager.get_statistics()
        text = f"Total: {stats['total_testcases']} test cases in {stats['total_files']} files"
        if stats['last_index_time']:
            text += f"\nLast indexed: {stats['last_index_time'][:19]}"
        self.stats_label.setText(text)
        
    def _on_text_changed(self):
        """Handle text change with debouncing"""
        # Restart debounce timer
        self.debounce_timer.stop()
        self.debounce_timer.start()
    
    def _perform_search(self):
        """Perform the actual search"""
        query = self.search_edit.text().strip()
        if not query:
            # If input is empty, don't search and keep last results
            return
        
        self.last_search_query = query
        self._search(query)
    
    def _search(self, query=None):
        """Execute search"""
        if query is None:
            query = self.search_edit.text().strip()
        
        if not query:
            return
            
        try:
            results = self.index_manager.search_testcases(query)
            self._display_results(results, query)
            # Trigger state change after search
            self.state_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"Error during search: {e}")
            
    def _display_results(self, results, query):
        """Display search results in tree structure showing full path from project root"""
        self.current_results = results
        self.results_model.clear()
        
        if not results:
            no_results_item = QStandardItem("No results found")
            no_results_item.setEditable(False)
            self.results_model.appendRow(no_results_item)
            return
            
        # Use the same project root as Project Explorer
        project_root = self.project_path
        
        # Create root node (same as Project Explorer)
        root_item = QStandardItem(os.path.basename(project_root))
        root_item.setEditable(False)
        root_item.setIcon(self.tree_builder.folder_icon)
        root_item.setData(project_root, Qt.UserRole)
        
        # Create a temporary model for the root node to build the tree structure
        temp_model = QStandardItemModel()
        
        # Build hierarchical structure for each result showing full path from project root
        processed_paths = set()
        
        for result in results:
            file_path = result['file_path']
            
            # Skip if we've already processed this file (avoid duplicates)
            if file_path in processed_paths:
                continue
            processed_paths.add(file_path)
            
            # Add file path to temporary model with full hierarchy from project root
            self.tree_builder.add_file_path_to_tree(
                temp_model, 
                file_path, 
                result_data=result, 
                file_icon=self.result_icon,
                project_root=project_root
            )
            
        # Move all items from temporary model to the root item
        invisible_root = temp_model.invisibleRootItem()
        for i in range(invisible_root.rowCount()):
            child = invisible_root.takeChild(i, 0)
            root_item.appendRow(child)
            i -= 1  # Adjust index after taking child
        
        # Add root item to the main model
        self.results_model.appendRow(root_item)
        
        # Expand tree to show results better
        self.results_tree.expandToDepth(20)  # Expand a few levels to show results
        
        # Update stats with result count
        self.stats_label.setText(f"Found {len(results)} test cases for '{query}'")
        
    def _clear_search(self):
        """Clear search - no longer used but kept for compatibility"""
        # This method is no longer used since we removed the clear button
        # but keeping it for potential future use
        self.search_edit.clear()
        # Don't clear results or reset statistics when input is cleared
        # Let the last search results remain visible
        # Trigger state change 
        self.state_changed.emit()
        
    def _on_double_click(self, index):
        """Handle double click on result"""
        item = self.results_model.itemFromIndex(index)
        if not item:
            return
            
        result = item.data(Qt.UserRole)
        if result and isinstance(result, dict) and 'file_path' in result:
            self.file_open_requested.emit(result['file_path'])
            
    def _open_context_menu(self, position):
        """Open context menu for results"""
        index = self.results_tree.indexAt(position)
        if not index.isValid():
            return
            
        item = self.results_model.itemFromIndex(index)
        result = item.data(Qt.UserRole)
        
        if not result or not isinstance(result, dict):
            return
            
        menu = QMenu()
        open_action = menu.addAction("Open File")
        open_dir_action = menu.addAction("Open Directory")
        
        action = menu.exec_(self.results_tree.viewport().mapToGlobal(position))
        
        if action == open_action:
            self.file_open_requested.emit(result['file_path'])
        elif action == open_dir_action:
            self._open_directory(result['file_path'])
            
    def _open_directory(self, file_path):
        """Open directory containing the file"""
        import subprocess
        import platform
        
        dir_path = os.path.dirname(file_path)
        
        try:
            if platform.system() == "Windows":
                os.startfile(dir_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", dir_path])
            else:  # Linux / Unix
                subprocess.Popen(["xdg-open", dir_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot open directory: {e}")
    
    def _rebuild_index(self):
        """Rebuild test case index"""
        try:
            self.rebuild_button.setEnabled(False)
            self.rebuild_button.setText("Rebuilding...")
            
            # Stop file watcher
            self.index_manager.stop_file_watcher()
            
            # Build index in background thread
            from PySide6.QtCore import QThread, Signal
            class RebuildThread(QThread):
                finished = Signal(int)
                error = Signal(str)
                
                def __init__(self, index_manager):
                    super().__init__()
                    self.index_manager = index_manager
                
                def run(self):
                    try:
                        count = self.index_manager.build_index(force_rebuild=True)
                        self.finished.emit(count)
                    except Exception as e:
                        self.error.emit(str(e))
            
            # Start background rebuild
            self.rebuild_thread = RebuildThread(self.index_manager)
            self.rebuild_thread.finished.connect(lambda count: self._on_rebuild_finished(count))
            self.rebuild_thread.error.connect(lambda error: self._on_rebuild_error(error))
            self.rebuild_thread.start()
            
        except Exception as e:
            self._on_rebuild_error(f"Error starting rebuild: {e}")
    
    def _on_rebuild_finished(self, count):
        """Handle rebuild completion"""
        self.rebuild_button.setEnabled(True)
        self.rebuild_button.setText("Rebuild Index")
        
        # Update statistics
        self._load_statistics()
        
        # If there was a search query, refresh results
        if self.last_search_query:
            self._search(self.last_search_query)
        
        # Show success message
        self.stats_label.setText(f"Rebuilt index: {count} files processed")
        self.state_changed.emit()
    
    def _on_rebuild_error(self, error):
        """Handle rebuild error"""
        self.rebuild_button.setEnabled(True)
        self.rebuild_button.setText("Rebuild Index")
        QMessageBox.critical(self, "Rebuild Error", f"Error rebuilding index: {error}")
        self.state_changed.emit()