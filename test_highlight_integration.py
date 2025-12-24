#!/usr/bin/env python3
"""测试关键字高亮功能"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'teshi'))

from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PySide6.QtGui import QAction
from teshi.utils.keyword_highlighter import KeywordHighlighter

class TestHighlightWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试关键字高亮")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 创建文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在这里输入文本进行测试...")
        
        # 添加一些示例文本
        sample_text = """这是一个测试文件。
包含关键字：登录、密码、用户名。
还有一些其他的内容。
测试登录功能和密码验证。
用户名和密码都是关键字。"""
        
        self.text_edit.setText(sample_text)
        layout.addWidget(self.text_edit)
        
        # 创建高亮器
        self.highlighter = KeywordHighlighter()
        
        # 设置一些测试关键字
        self.highlighter.set_keywords(["登录", "密码", "用户名"])
        
        # 应用高亮
        self.highlighter.highlight_text(self.text_edit)
        
        # 添加菜单
        menubar = self.menuBar()
        
        # 测试菜单
        test_menu = menubar.addMenu("测试")
        
        # 测试不同关键字
        test_keywords_action = QAction("测试关键字: 测试", self)
        test_keywords_action.triggered.connect(lambda: self.test_keywords(["测试"]))
        test_menu.addAction(test_keywords_action)
        
        test_multi_action = QAction("测试多关键字: 登录, 密码, 用户名", self)
        test_multi_action.triggered.connect(lambda: self.test_keywords(["登录", "密码", "用户名"]))
        test_menu.addAction(test_multi_action)
        
        clear_action = QAction("清除高亮", self)
        clear_action.triggered.connect(self.clear_highlight)
        test_menu.addAction(clear_action)
        
    def test_keywords(self, keywords):
        """测试指定的关键字"""
        self.highlighter.set_keywords(keywords)
        self.highlighter.highlight_text(self.text_edit)
        print(f"应用关键字高亮: {keywords}")
        
    def clear_highlight(self):
        """清除高亮"""
        self.highlighter.clear_keywords()
        self.highlighter.highlight_text(self.text_edit)
        print("清除高亮")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestHighlightWindow()
    window.show()
    sys.exit(app.exec())