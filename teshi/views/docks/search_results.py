import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QTreeView, QMenu, QMessageBox, QLabel, QFrame, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon

from teshi.utils.testcase_index_manager import TestCaseIndexManager
from teshi.utils.resource_path import resource_path


class SearchResultsDock(QWidget):
    """Search results dock widget"""
    
    file_open_requested = Signal(str)
    state_changed = Signal()
    
    def __init__(self, index_manager: TestCaseIndexManager, parent=None):
        super().__init__(parent)
        self.index_manager = index_manager
        self.current_results = []
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
        self.folder_icon = QIcon(resource_path("assets/icons/folder.png"))
        self.file_icon = QIcon(resource_path("assets/icons/testcase_normal.png"))
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
        """Display search results in tree structure"""
        self.current_results = results
        self.results_model.clear()
        
        if not results:
            no_results_item = QStandardItem("No results found")
            no_results_item.setEditable(False)
            self.results_model.appendRow(no_results_item)
            return
            
        # Group results by directory
        dir_structure = {}
        
        for result in results:
            file_path = result['file_path']
            dir_name = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            
            if dir_name not in dir_structure:
                dir_structure[dir_name] = []
            dir_structure[dir_name].append((file_name, result))
            
        # Build tree
        for dir_name, files in sorted(dir_structure.items()):
            # Create directory item
            dir_display_name = os.path.basename(dir_name) if os.path.basename(dir_name) else "Root"
            dir_item = QStandardItem(f"{dir_display_name} ({len(files)})")
            dir_item.setEditable(False)
            dir_item.setIcon(self.folder_icon)
            dir_item.setData(dir_name, Qt.UserRole)
            
            # Add files to directory
            for file_name, result in files:
                # Use search highlighted name if available
                display_name = result.get('name_snippet', result['name'])
                # For tree display, remove HTML tags
                clean_name = display_name.replace("<mark>", "").replace("</mark>", "") if "<mark>" in display_name else display_name
                
                file_item = QStandardItem(clean_name)
                file_item.setEditable(False)
                file_item.setIcon(self.result_icon)
                file_item.setData(result, Qt.UserRole)  # Store complete result
                
                dir_item.appendRow(file_item)
                
            self.results_model.appendRow(dir_item)
            
        # Expand first level
        self.results_tree.expandToDepth(0)
        
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