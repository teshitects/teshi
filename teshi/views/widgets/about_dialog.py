from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QVBoxLayout, QDialog, QHBoxLayout
from PySide6.QtCore import Qt
from teshi.utils.resource_path import resource_path


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About Teshi")
        self.setWindowIcon(QIcon(resource_path("assets/teshi_icon64.png")))
        self.setFixedSize(500, 350)

        self.setStyleSheet("background-color: #2b2b2b; color: white;")

        layout = QVBoxLayout(self)

        title_label = QLabel("Teshi")

        version_label = QLabel("Version: 2025.10.31")

        copyright_label = QLabel("Copyright © 2025 Teshi. All rights reserved.")

        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addWidget(copyright_label)

        title_label.setAlignment(Qt.AlignCenter)
        version_label.setAlignment(Qt.AlignCenter)
        copyright_label.setAlignment(Qt.AlignCenter)

        title_label.setStyleSheet("font-size: 20px;")

        version_label.setStyleSheet("color: #888888;")
        copyright_label.setStyleSheet("color: #888888;")

        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        license_label = QLabel("Open Source License: Apache-2.0")
        license_label.setStyleSheet("color: #888888;")
        layout.addWidget(license_label)

        pyside_license_label = QLabel("PySide6 License: LGPL v3")
        pyside_license_label.setStyleSheet("color: #888888;")
        layout.addWidget(pyside_license_label)


