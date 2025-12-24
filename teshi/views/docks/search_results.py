import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QTreeView, QMenu, QMessageBox, QLabel, QFrame, QHeaderView
)
from PySide6.QtCore import Qt, Signal
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
        self.search_edit.returnPressed.connect(self._search)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self._search)
        self.search_btn.setMaximumWidth(60)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_search)
        self.clear_btn.setMaximumWidth(50)
        
        search_layout.addWidget(self.search_edit, 1)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.clear_btn)
        
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
        
    def _search(self):
        """Execute search"""
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
        self.results_tree.expandToDepth(2)  # Expand a few levels to show results
        
        # Update stats with result count
        self.stats_label.setText(f"Found {len(results)} test cases for '{query}'")
        
    def _clear_search(self):
        """Clear search"""
        self.search_edit.clear()
        self.results_model.clear()
        self.current_results = []
        self._load_statistics()
        # Trigger state change after clearing
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