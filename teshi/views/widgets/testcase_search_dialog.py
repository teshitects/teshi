from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QListWidget, QListWidgetItem, QLabel, QTextEdit, QWidget,
    QSplitter, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextDocument, QTextCharFormat, QColor, QPalette

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
        self._setup_highlight_format()
    
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
        self.highlight_format = None
        self.current_query = ""
    
    def _setup_highlight_format(self):
        """Setup highlight format for search results"""
        self.highlight_format = QTextCharFormat()
        # Determine theme-appropriate highlight color
        self.highlight_color = self._get_theme_appropriate_highlight_color()
        self.highlight_format.setBackground(self.highlight_color)
    
    def _get_theme_appropriate_highlight_color(self):
        """Get appropriate highlight color based on current theme"""
        # Check if dark mode is active by checking the palette
        palette = QApplication.palette()
        window_bg = palette.color(QPalette.Window)
        window_text = palette.color(QPalette.WindowText)
        
        # Calculate luminance to determine if theme is dark or light
        # Using relative luminance formula: 0.299*R + 0.587*G + 0.114*B
        luminance = (0.299 * window_bg.red() + 0.587 * window_bg.green() + 0.114 * window_bg.blue()) / 255
        
        # If luminance is less than 0.5, it's likely a dark theme
        if luminance < 0.5:
            # Dark theme: use a much brighter and more saturated highlight color
            # Use a bright orange-yellow that provides excellent contrast on dark backgrounds
            return QColor(255, 180, 0)  # Bright amber/orange-yellow
        else:
            # Light theme: use a softer yellow that doesn't overpower white text
            return QColor(255, 255, 150)  # Light yellow
    
    def _get_highlight_css_color(self):
        """Get CSS color string for HTML highlighting"""
        return self.highlight_color.name()  # QColor.name() already returns hex with #
    
    def _html_to_rich_text(self, html_text, use_plain_fallback=True):
        """Convert HTML with <mark> tags to rich text with highlighting"""
        if not html_text:
            return ""
        
        # If no mark tags, return plain text
        if "<mark>" not in html_text:
            return html_text
        
        # Create a text document to handle the conversion
        doc = QTextDocument()
        
        # Get theme-appropriate highlight color
        highlight_css = self._get_highlight_css_color()
        
        # Replace <mark> tags with spans that have a background color
        # Qt's rich text engine supports basic HTML including CSS
        styled_html = html_text.replace(
            "<mark>", 
            f'<span style="background-color: {highlight_css};">'
        ).replace(
            "</mark>", 
            "</span>"
        )
        
        # Set the HTML to the document
        doc.setHtml(styled_html)
        
        # Return as plain text if there are issues with rich text
        if use_plain_fallback and doc.isEmpty():
            # Fallback: remove mark tags and return plain text
            return html_text.replace("<mark>", "").replace("</mark>", "")
        
        return doc.toHtml()
    
    def _apply_highlight_to_textedit(self, text_edit, text, snippet_text=None):
        """Apply highlighting to a QTextEdit widget"""
        if not text and not snippet_text:
            text_edit.clear()
            return
        
        # Re-detect theme and update highlight color each time
        self._setup_highlight_format()
        
        # Use snippet if available, otherwise use plain text
        display_text = snippet_text if snippet_text else text
        
        if "<mark>" in display_text:
            # Convert HTML with highlighting to rich text
            highlight_css = self._get_highlight_css_color()
            styled_html = display_text.replace(
                "<mark>", 
                f'<span style="background-color: {highlight_css};">'
            ).replace(
                "</mark>", 
                "</span>"
            )
            text_edit.setHtml(styled_html)
        else:
            # No highlighting needed, use plain text
            text_edit.setPlainText(display_text if display_text else "")
    
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
        
        self.current_query = query
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
            # For the list item, we'll remove HTML tags for cleaner display
            clean_name = display_name.replace("<mark>", "").replace("</mark>", "") if "<mark>" in display_name else display_name
            item = QListWidgetItem(clean_name)
            
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
        
        # Apply highlighting to relevant fields
        self._apply_highlight_to_textedit(
            self.preconditions_edit, 
            result['preconditions'], 
            result.get('preconditions_snippet')
        )
        self._apply_highlight_to_textedit(
            self.steps_edit, 
            result['steps'], 
            result.get('steps_snippet')
        )
        self._apply_highlight_to_textedit(
            self.expected_results_edit, 
            result['expected_results'], 
            result.get('expected_results_snippet')
        )
        self._apply_highlight_to_textedit(
            self.notes_edit, 
            result['notes'], 
            result.get('notes_snippet')  # Now notes_snippet is provided by index manager
        )
    
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
        self.current_query = ""
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