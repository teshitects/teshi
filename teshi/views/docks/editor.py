#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, re
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit
from PySide6.QtGui import QTextCharFormat, QColor, QFont, QSyntaxHighlighter
from PySide6.QtCore import Qt

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        # Header formats (H1-H6)
        self.f_headers = []
        header_colors = ["#1f6feb", "#2b6cb0", "#3b82f6", "#0ea5e9", "#06b6d4", "#22c55e"]
        header_sizes = [20, 18, 16, 15, 14, 13]
        for color, size in zip(header_colors, header_sizes):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            fmt.setFontWeight(QFont.Bold)
            fmt.setFontPointSize(size)
            self.f_headers.append(fmt)

        # Inline formats
        self.f_bold = QTextCharFormat()
        self.f_bold.setFontWeight(QFont.Bold)

        self.f_italic = QTextCharFormat()
        self.f_italic.setFontItalic(True)

        self.f_strike = QTextCharFormat()
        self.f_strike.setFontStrikeOut(True)
        self.f_strike.setForeground(QColor("#718096"))

        self.f_inline_code = QTextCharFormat()
        self.f_inline_code.setFontFamilies(["Monospace"])
        self.f_inline_code.setBackground(QColor("#edf2f7"))
        self.f_inline_code.setForeground(QColor("#2d3748"))

        # YAML front matter
        self.f_yaml_bg = QTextCharFormat()
        self.f_yaml_bg.setBackground(QColor("#f0f0f0"))
        self.f_yaml_bg.setForeground(QColor("#4a5568"))

        self.f_yaml_key = QTextCharFormat()
        self.f_yaml_key.setForeground(QColor("#718096"))
        self.f_yaml_key.setFontWeight(QFont.Bold)

        self.f_yaml_value = QTextCharFormat()
        self.f_yaml_value.setForeground(QColor("#718096"))

        # Regex patterns
        self.re_header = [
            re.compile(r"^#{1}\s+.*"),
            re.compile(r"^#{2}\s+.*"),
            re.compile(r"^#{3}\s+.*"),
            re.compile(r"^#{4}\s+.*"),
            re.compile(r"^#{5}\s+.*"),
            re.compile(r"^#{6}\s+.*"),
        ]
        self.re_bold = re.compile(r"\*\*(.+?)\*\*")
        self.re_italic = re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)")
        self.re_strike = re.compile(r"~~(.+?)~~")
        self.re_inline_code = re.compile(r"`([^`]+)`")
        self.re_yaml_kv = re.compile(r"^([A-Za-z0-9_\-\.]+)\s*:\s*(.*)$")

    def highlightBlock(self, text: str):
        # YAML front matter detection
        if self.currentBlock().blockNumber() == 0 and text.strip() == "---":
            self.setFormat(0, len(text), self.f_yaml_bg)
            self.setCurrentBlockState(1)
            return
        if self.previousBlockState() == 1:
            self.setFormat(0, len(text), self.f_yaml_bg)
            m = self.re_yaml_kv.match(text)
            if m:
                key, val = m.group(1), m.group(2)
                self.setFormat(0, len(key), self.f_yaml_key)
                colon_idx = text.find(":")
                if colon_idx >= 0:
                    self.setFormat(colon_idx, 1, self.f_yaml_key)
                if colon_idx + 1 < len(text):
                    self.setFormat(colon_idx + 1, len(text) - colon_idx - 1, self.f_yaml_value)
            if text.strip() == "---":
                self.setFormat(0, len(text), self.f_yaml_bg)
                self.setCurrentBlockState(0)
                return
            self.setCurrentBlockState(1)
            return

        # Headers
        for i, rx in enumerate(self.re_header):
            if rx.match(text):
                self.setFormat(0, len(text), self.f_headers[i])
                return

        # Bold
        for m in self.re_bold.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.f_bold)

        # Italic
        for m in self.re_italic.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.f_italic)

        # Strike-through
        for m in self.re_strike.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.f_strike)

        # Inline code
        for m in self.re_inline_code.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.f_inline_code)


class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-time Preview Markdown Editor (Multi-level Headers + YAML)")
        self.resize(900, 650)

        self.editor = QTextEdit()
        self.editor.setPlainText("""---
title: 'Example Case'
level: 'Normal'
domain: 'Login'
automated: false
---

# H1 Header

## H2 Header

### H3 Header

#### H4 Header

##### H5 Header

###### H6 Header

Supports **bold**, *italic*, ~~strikethrough~~, `inline code`

""")
        self.setCentralWidget(self.editor)

        # Attach highlighter
        self.highlighter = MarkdownHighlighter(self.editor.document())


def main():
    app = QApplication(sys.argv)
    win = EditorWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
