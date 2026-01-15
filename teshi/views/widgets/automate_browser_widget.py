from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QLabel, 
    QLineEdit, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, Signal
import os
import json
from pathlib import Path

class AutomateBrowserWidget(QWidget):
    """
    Browser widget for Automate Mode.
    Displays:
    1. Project-wide used nodes (from .ipynb files) with search.
    2. Current Canvas used nodes (sorted by execution order).
    """
    
    nodeSelected = Signal(str) # Emits code when a node is clicked, maybe?

    def __init__(self, project_dir, parent=None):
        super().__init__(parent)
        self.project_dir = project_dir
        self.extracted_nodes = {} # {title: code}
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter to resize top/bottom parts
        self.splitter = QSplitter(Qt.Vertical)
        
        # --- Top Section: Project Nodes ---
        self.project_group = QGroupBox("Project Nodes")
        project_layout = QVBoxLayout(self.project_group)
        project_layout.setContentsMargins(5, 5, 5, 5)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search nodes...")
        self.search_bar.textChanged.connect(self.filter_project_nodes)
        project_layout.addWidget(self.search_bar)
        
        # List Widget
        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self.on_project_item_clicked)
        project_layout.addWidget(self.project_list)
        
        self.splitter.addWidget(self.project_group)
        
        # --- Bottom Section: Canvas Nodes (Execution Order) ---
        self.canvas_group = QGroupBox("Execution Order")
        canvas_layout = QVBoxLayout(self.canvas_group)
        canvas_layout.setContentsMargins(5, 5, 5, 5)
        
        self.canvas_list = QListWidget()
        canvas_layout.addWidget(self.canvas_list)
        
        self.splitter.addWidget(self.canvas_group)
        
        layout.addWidget(self.splitter)
        
        # Initial scan
        self.refresh_project_nodes()

    def refresh_project_nodes(self):
        """Scans project directory for .ipynb files and extracts node titles."""
        self.project_list.clear()
        self.extracted_nodes = {}
        
        if not self.project_dir or not os.path.exists(self.project_dir):
            return

        # Simple recursive scan
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(".ipynb"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            notebook = json.load(f)
                            
                        cells = notebook.get('cells', [])
                        for cell in cells:
                            if cell.get('cell_type') == 'code':
                                source = cell.get('source', [])
                                if isinstance(source, list):
                                    source = "".join(source)
                                
                                if source.strip():
                                    title = source.split('\n')[0].strip()
                                    if title and title not in self.extracted_nodes:
                                        self.extracted_nodes[title] = source
                                        self.project_list.addItem(title)
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        
        self.project_list.sortItems()

    def filter_project_nodes(self, text):
        """Filters the project list based on search text."""
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def update_canvas_nodes(self, node_titles):
        """Updates the list of nodes currently on the canvas (execution order)."""
        self.canvas_list.clear()
        for title in node_titles:
            self.canvas_list.addItem(title)

    def on_project_item_clicked(self, item):
        title = item.text()
        if title in self.extracted_nodes:
            # Logic to handle click (e.g. copy code, or just show info)
            # For now, maybe just emit specific signal if needed, 
            # or users can drag and drop if we implement that later.
            pass
