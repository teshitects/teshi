import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt


class ProjectSelectPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Welcome to Teshi")
        self.setGeometry(300, 150, 785, 603)
        self.setStyleSheet("background-color: #2b2d30;")

        self.setContentsMargins(0,0,0,0)

        self.setWindowIcon(QIcon("assets/teshi_icon64.png"))

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0,0,0,0)

        left_layout = QHBoxLayout()
        left_layout.setSpacing(0)
        name_label = QLabel("Teshi")
        name_label.setAlignment(Qt.AlignLeft)
        name_label.setFixedWidth(226)
        left_layout.addWidget(name_label)

        right_layout = QHBoxLayout()
        right_layout.setSpacing(0)
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #1e1f22;")
        right_layout.addWidget(right_container)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)


