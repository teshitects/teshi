#!/usr/bin/env python3
"""
Test script for keyword highlighting functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from teshi.utils.keyword_highlighter import KeywordHighlighter


class TestHighlightWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keyword Highlight Test")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout(self)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("""This is a test document for keyword highlighting.

We want to highlight important words like "login" and "password".

The login button should be prominent.
User password must be secure.

Another login attempt failed.
Password validation is important.""")
        
        layout.addWidget(self.text_edit)
        
        # Highlight buttons
        highlight_btn = QPushButton("Highlight 'login', 'password'")
        highlight_btn.clicked.connect(self.test_highlight)
        layout.addWidget(highlight_btn)
        
        clear_btn = QPushButton("Clear Highlighting")
        clear_btn.clicked.connect(self.clear_highlight)
        layout.addWidget(clear_btn)
        
        # Initialize highlighter
        self.highlighter = KeywordHighlighter()
        
    def test_highlight(self):
        keywords = ["login", "password"]
        self.highlighter.set_keywords(keywords)
        count = self.highlighter.highlight_text(self.text_edit)
        print(f"Highlighted {count} instances")
        
    def clear_highlight(self):
        self.highlighter.clear_keywords()
        self.highlighter.highlight_text(self.text_edit)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TestHighlightWindow()
    window.show()
    
    sys.exit(app.exec())