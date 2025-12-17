from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QListWidget, QListWidgetItem, QLabel, QTextEdit, QWidget,
    QSplitter, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from teshi.utils.testcase_index_manager import TestCaseIndexManager


class TestcaseSearchDialog(QDialog):
    """Test case search dialog"""
    
    def __init__(self, index_manager: TestCaseIndexManager, parent=None):
        super().__init__(parent)
        self.index_manager = index_manager
        self.setWindowTitle("Search Test Cases")
        self.setModal(False)
        self.resize(800, 600)
        
        self._setup_ui()
        self._load_statistics()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Search area
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter search terms...")
        self.search_edit.returnPressed.connect(self._search)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self._search)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_search)
        
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_edit, 1)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.clear_btn)
        
        layout.addLayout(search_layout)
        
        # Statistics information
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.stats_label)
        
        # Main content area
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Search results list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self._on_result_selected)
        left_layout.addWidget(self.results_list)
        
        # Right side: Detailed information
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        
        # Test case name
        self.name_label = QLabel()
        self.name_label.setFont(QFont("", 12, QFont.Bold))
        self.details_layout.addWidget(self.name_label)
        
        # File path
        self.path_label = QLabel()
        self.path_label.setStyleSheet("color: #666; font-size: 10px;")
        self.details_layout.addWidget(self.path_label)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.details_layout.addWidget(line)
        
        # Various fields
        self.preconditions_edit = QTextEdit()
        self.preconditions_edit.setReadOnly(True)
        self.preconditions_edit.setMaximumHeight(100)
        self.details_layout.addWidget(QLabel("Preconditions:"))
        self.details_layout.addWidget(self.preconditions_edit)
        
        self.steps_edit = QTextEdit()
        self.steps_edit.setReadOnly(True)
        self.steps_edit.setMaximumHeight(150)
        self.details_layout.addWidget(QLabel("Steps:"))
        self.details_layout.addWidget(self.steps_edit)
        
        self.expected_results_edit = QTextEdit()
        self.expected_results_edit.setReadOnly(True)
        self.expected_results_edit.setMaximumHeight(100)
        self.details_layout.addWidget(QLabel("Expected Results:"))
        self.details_layout.addWidget(self.expected_results_edit)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(True)
        self.notes_edit.setMaximumHeight(80)
        self.details_layout.addWidget(QLabel("Notes:"))
        self.details_layout.addWidget(self.notes_edit)
        
        # Open file button
        self.open_file_btn = QPushButton("Open File")
        self.open_file_btn.clicked.connect(self._open_file)
        self.open_file_btn.setEnabled(False)
        self.details_layout.addWidget(self.open_file_btn)
        
        right_layout.addWidget(self.details_widget)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # Button bar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.hide)  # Hide instead of accept for non-modal dialog
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Initial state
        self.current_result = None
    
    def _load_statistics(self):
        """Load statistics information"""
        stats = self.index_manager.get_statistics()
        text = f"Total: {stats['total_testcases']} test cases in {stats['total_files']} files"
        if stats['last_index_time']:
            text += f" | Last indexed: {stats['last_index_time'][:19]}"
        self.stats_label.setText(text)
    
    def _search(self):
        """Execute search"""
        query = self.search_edit.text().strip()
        if not query:
            return
        
        try:
            results = self.index_manager.search_testcases(query)
            self._display_results(results, query)
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"Error during search: {e}")
    
    def _display_results(self, results, query):
        """Display search results"""
        self.results_list.clear()
        
        if not results:
            self.results_list.addItem(QListWidgetItem("No results found"))
            return
        
        for result in results:
            # Use search highlighted name
            display_name = result.get('name_snippet', result['name'])
            item = QListWidgetItem(display_name)
            
            # Store complete result data
            item.setData(Qt.UserRole, result)
            
            # Set tooltip to show file path
            item.setToolTip(result['file_path'])
            
            self.results_list.addItem(item)
        
        # Select first result
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
            self._on_result_selected(self.results_list.currentItem())
    
    def _on_result_selected(self, item):
        """When search result is selected"""
        if not item or not item.data(Qt.UserRole):
            self._clear_details()
            return
        
        self.current_result = item.data(Qt.UserRole)
        self._display_details(self.current_result)
        self.open_file_btn.setEnabled(True)
    
    def _display_details(self, result):
        """Display test case detailed information"""
        self.name_label.setText(result['name'])
        self.path_label.setText(result['file_path'])
        
        self.preconditions_edit.setPlainText(result['preconditions'] or "")
        self.steps_edit.setPlainText(result['steps'] or "")
        self.expected_results_edit.setPlainText(result['expected_results'] or "")
        self.notes_edit.setPlainText(result['notes'] or "")
    
    def _clear_details(self):
        """Clear detailed information"""
        self.name_label.setText("")
        self.path_label.setText("")
        self.preconditions_edit.clear()
        self.steps_edit.clear()
        self.expected_results_edit.clear()
        self.notes_edit.clear()
        self.open_file_btn.setEnabled(False)
        self.current_result = None
    
    def _clear_search(self):
        """Clear search"""
        self.search_edit.clear()
        self.results_list.clear()
        self._clear_details()
    
    def _open_file(self):
        """Open file"""
        if not self.current_result:
            return
        
        file_path = self.current_result['file_path']
        
        # Open file through parent window
        parent = self.parent()
        if hasattr(parent, 'open_file_in_tab'):
            parent.open_file_in_tab(file_path)
            # Don't close the dialog for non-modal mode
        else:
            QMessageBox.information(self, "Open File", f"File path: {file_path}")
    
    def keyPressEvent(self, event):
        """Handle keyboard events"""
        if event.key() == Qt.Key_Escape:
            self.hide()  # Hide instead of accept for non-modal dialog
        elif event.key() == Qt.Key_F and event.modifiers() & Qt.ControlModifier:
            self.search_edit.setFocus()
            self.search_edit.selectAll()
        else:
            super().keyPressEvent(event)