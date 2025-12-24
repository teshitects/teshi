from typing import List, Tuple, Optional
import re
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor, QFont, QTextDocument
from PySide6.QtCore import Qt


class KeywordHighlighter:
    """关键字高亮器，支持在文本中高亮单个或多个关键字"""
    
    def __init__(self):
        self.keywords = []
        self.highlight_format = QTextCharFormat()
        self._setup_default_format()
    
    def _setup_default_format(self):
        """设置默认高亮格式"""
        # 黄色背景，黑色文字
        self.highlight_format.setBackground(QColor(255, 255, 0))
        self.highlight_format.setForeground(QColor(0, 0, 0))
        # 加粗
        font = QFont()
        font.setBold(True)
        self.highlight_format.setFont(font)
    
    def set_keywords(self, keywords: List[str]):
        """设置要高亮的关键字列表"""
        self.keywords = [keyword.strip() for keyword in keywords if keyword.strip()]
    
    def add_keyword(self, keyword: str):
        """添加单个关键字"""
        keyword = keyword.strip()
        if keyword and keyword not in self.keywords:
            self.keywords.append(keyword)
    
    def remove_keyword(self, keyword: str):
        """移除关键字"""
        if keyword in self.keywords:
            self.keywords.remove(keyword)
    
    def clear_keywords(self):
        """清除所有关键字"""
        self.keywords.clear()
    
    def set_highlight_color(self, color: QColor):
        """设置高亮颜色"""
        self.highlight_format.setBackground(color)
    
    def highlight_text(self, text_edit) -> int:
        """
        在QTextEdit中高亮关键字
        
        Args:
            text_edit: QTextEdit组件
            
        Returns:
            int: 高亮的关键字数量
        """
        if not self.keywords:
            return 0
        
        document = text_edit.document()
        cursor = QTextCursor(document)
        
        # 清除之前的高亮
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())
        
        highlight_count = 0
        
        # 对每个关键字进行高亮
        for keyword in self.keywords:
            if not keyword.strip():
                continue
                
            # 从文档开头开始搜索
            cursor.movePosition(QTextCursor.Start)
            
            while True:
                # 使用QTextDocument的find方法进行不区分大小写搜索
                found_cursor = document.find(keyword, cursor, QTextDocument.FindWholeWords)
                
                if found_cursor.isNull():
                    # 如果没找到完整词，尝试部分匹配
                    found_cursor = document.find(keyword, cursor)
                
                if found_cursor.isNull():
                    break
                
                # 应用高亮格式
                found_cursor.mergeCharFormat(self.highlight_format)
                highlight_count += 1
                
                # 移动到找到位置的下一个字符继续搜索
                cursor.setPosition(found_cursor.position() + 1)
                
                # 防止无限循环
                if cursor.atEnd():
                    break
        
        return highlight_count
    
    def highlight_html_content(self, content: str) -> str:
        """
        在HTML内容中高亮关键字
        
        Args:
            content: HTML内容
            
        Returns:
            str: 包含高亮标签的HTML内容
        """
        if not self.keywords:
            return content
        
        # 获取高亮颜色的RGB值
        bg_color = self.highlight_format.background().color()
        fg_color = self.highlight_format.foreground().color()
        highlight_style = f'background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}); color: rgb({fg_color.red()}, {fg_color.green()}, {fg_color.blue()}); font-weight: bold;'
        
        highlighted_content = content
        
        # 对每个关键字进行高亮
        for keyword in self.keywords:
            # 使用正则表达式进行不区分大小写的替换
            pattern = re.compile(f'({re.escape(keyword)})', re.IGNORECASE)
            replacement = f'<span style="{highlight_style}">\\1</span>'
            highlighted_content = pattern.sub(replacement, highlighted_content)
        
        return highlighted_content
    
    def find_keyword_positions(self, content: str) -> List[Tuple[str, int, int]]:
        """
        查找关键字在文本中的位置
        
        Args:
            content: 文本内容
            
        Returns:
            List[Tuple[str, int, int]]: (keyword, start_pos, end_pos) 的列表
        """
        positions = []
        
        for keyword in self.keywords:
            # 使用正则表达式查找所有匹配项
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            for match in pattern.finditer(content):
                start_pos = match.start()
                end_pos = match.end()
                positions.append((keyword, start_pos, end_pos))
        
        # 按位置排序
        positions.sort(key=lambda x: x[1])
        return positions