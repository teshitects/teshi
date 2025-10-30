# Import required modules
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QFrame, QSizePolicy
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt


# Class for the project selection page UI
class ProjectSelectPage(QWidget):
    def __init__(self):
        super().__init__()

        # Set window title, geometry, and background color
        self.setWindowTitle("Welcome to Teshi")
        self.setGeometry(300, 150, 785, 603)
        self.setStyleSheet("background-color: #2b2d30;")

        # Set window margins and icon
        self.setContentsMargins(0,0,0,0)
        self.setWindowIcon(QIcon("assets/teshi_icon64.png"))

        # Initialize main layout with horizontal alignment
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0,0,0,0)

        # Initialize left layout for logo and version info
        left_layout = QHBoxLayout()
        left_layout.setSpacing(0)

        # Logo container with icon and name/version
        top_left_logo = QWidget()
        top_left_logo_layout = QHBoxLayout()
        top_left_logo.setLayout(top_left_logo_layout)
        top_left_logo.setFixedWidth(226)
        top_left_logo.setFixedHeight(80)

        # Icon label for the application logo
        icon_label = QLabel()
        icon_label.setPixmap(QIcon("assets/teshi_icon48.png").pixmap(48, 48))
        icon_label.setFixedSize(48, 48)
        top_left_logo_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Panel for application name and version
        name_version_panel = QWidget()
        name_version_panel_layout = QVBoxLayout()
        name_version_panel.setLayout(name_version_panel_layout)
        top_left_logo_layout.addWidget(name_version_panel, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        name_label = QLabel("Teshi")
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        version_label = QLabel("2025.10.31")
        version_label.setFont(QFont("Microsoft YaHei", 7))
        version_label.setStyleSheet("color: gray;")
        name_version_panel_layout.addWidget(name_label)
        name_version_panel_layout.addWidget(version_label)

        left_layout.addWidget(top_left_logo, 0, Qt.AlignmentFlag.AlignTop)
        left_layout.setContentsMargins(15,15,15,15)

        # Initialize right layout for buttons and project list
        right_layout = QHBoxLayout()
        right_layout.setSpacing(0)
        right_container = QWidget()
        right_container_layout = QVBoxLayout()
        right_container.setLayout(right_container_layout)
        right_container_layout.setSpacing(0)
        right_container_layout.setContentsMargins(0,0,0,0)
        right_container.setStyleSheet("background-color: #1e1f22;")
        right_layout.addWidget(right_container)

        # Container for "New Project" and "Open" buttons
        top_right_button_container = QWidget()
        top_right_button_container_layout = QHBoxLayout()
        top_right_button_container.setLayout(top_right_button_container_layout)

        # "New Project" button
        new_project_button = QPushButton("New Project")
        new_project_button.setFixedSize(120, 30)
        new_project_button.setStyleSheet("background-color: #2b2d30")
        right_container_layout.addWidget(top_right_button_container, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # "Open" button
        open_button = QPushButton("Open")
        open_button.setFixedSize(120, 30)
        open_button.setStyleSheet("background-color: #2b2d30")
        right_container_layout.addWidget(open_button, 0, Qt.AlignmentFlag.AlignRight)

        top_right_button_container_layout.addWidget(new_project_button)
        top_right_button_container_layout.addWidget(open_button)

        # Add a separator line
        right_container_layout.setContentsMargins(30, 0, 30, 0)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setFixedHeight(1)
        line.setStyleSheet("color: gray;")
        right_container_layout.addWidget(line)

        # Container for the project list
        project_list_container = QWidget()
        project_list_container_layout = QVBoxLayout()
        project_list_container_layout.setContentsMargins(30, 10, 30, 0)
        project_list_container_layout.setSpacing(0)

        # Generate project labels (mock data)
        for i in range(10):
            label = QLabel(f"  Project {i+1}")
            label.setCursor(Qt.PointingHandCursor)
            label.setStyleSheet("""
                QLabel:hover {
                    background-color: #2e436e;
                }
            """)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            project_list_container_layout.addWidget(label, 0)

        project_list_container.setLayout(project_list_container_layout)
        right_container_layout.addWidget(project_list_container, 1)

        # Add left and right layouts to the main layout
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)
