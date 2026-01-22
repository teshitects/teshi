
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QRegularExpression

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Keyword Format (e.g., def, class, return, import) - Orange
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#FF8C00"))  # DarkOrange
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield"
        ]
        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.highlighting_rules.append((pattern, keyword_format))

        # String Format (Single and Double quotes) - Green
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#6A8759"))
        self.highlighting_rules.append((QRegularExpression("\".*\""), string_format))
        self.highlighting_rules.append((QRegularExpression("'.*'"), string_format))

        # Comment Format (# comment) - Grey
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))
        self.highlighting_rules.append((QRegularExpression("#[^\n]*"), comment_format))

        # Number Format - Blue
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#6897BB"))
        self.highlighting_rules.append((QRegularExpression("\\b[0-9]+\\b"), number_format))
        
        # Decorator Format (@decorator) - Yellow-ish
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#BBB529"))
        self.highlighting_rules.append((QRegularExpression("@[a-zA-Z0-9_]+"), decorator_format))

        # Function Definition Name - Yellow
        # self.highlighting_rules.append((QRegularExpression("(?<=def\s)\w+"), decorator_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            match_iterator = expression.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
