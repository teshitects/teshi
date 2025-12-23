# Import required modules
import os
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QFrame, QSizePolicy, QDialog, \
    QLineEdit, QFormLayout, QFileDialog, QDialogButtonBox
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt
from teshi.utils.project_manager import ProjectManager
from teshi.utils.resource_path import resource_path


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
        self.setWindowIcon(QIcon(resource_path("assets/teshi_icon64.png")))

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
        icon_label.setPixmap(QIcon(resource_path("assets/teshi_icon48.png")).pixmap(48, 48))
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
        new_project_button.clicked.connect(self.show_new_project_dialog)
        right_container_layout.addWidget(top_right_button_container, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # "Open" button
        open_button = QPushButton("Open")
        open_button.setFixedSize(120, 30)
        open_button.setStyleSheet("background-color: #2b2d30")
        open_button.clicked.connect(self.show_open_project_dialog)
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
        project_list_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        project_list_container_layout.setSpacing(0)

        # Load and display saved projects
        project_manager = ProjectManager()
        projects = project_manager.load_projects()
        for project in projects:
            label = QLabel(f"  {project['name']}\n  <br/><span style='color: gray; font-size: 8pt;'>{project['path']}</span>")
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setCursor(Qt.PointingHandCursor)
            label.setStyleSheet("""
                QLabel:hover {
                    background-color: #2e436e;
                }
            """)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # Allow flexible height for each project
            label.setFixedHeight(50)
            label.mousePressEvent = lambda event, path=project['path']: self.open_project(path)
            project_list_container_layout.addWidget(label, 0)

        project_list_container.setLayout(project_list_container_layout)
        right_container_layout.addWidget(project_list_container, 1)

        # Add left and right layouts to the main layout
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def show_new_project_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("New Project")
        dialog.setFixedSize(600, 200)

        layout = QFormLayout()

        name_edit = QLineEdit()
        # Set Default Project Folder
        path_edit = QLineEdit()
        default_path = os.path.join(os.path.expanduser("~"), "Documents", "TeshiProjects")
        path_edit.setText(default_path)

        # Connect name_edit text change to update path_edit
        def update_path(text):
            if text:
                path_edit.setText(os.path.join(default_path, text))
            else:
                path_edit.setText(default_path)
        name_edit.textChanged.connect(update_path)

        layout.addRow("Project Name:", name_edit)
        layout.addRow("Project Path:", path_edit)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            project_manager = ProjectManager()
            # Add project to project manager
            project_manager.add_project(name_edit.text(), path_edit.text())
            os.makedirs(path_edit.text(), exist_ok=True)
            self.close()
            from teshi.views.main_window import MainWindow
            main_window = MainWindow(name_edit.text(), path_edit.text())
            main_window.show()

    def show_open_project_dialog(self):
        """
        Open a dialog to select a project folder and add it to the project manager.
        Closes the current window after selection.
        """
        default_path = os.path.join(os.path.expanduser("~"), "Documents", "TeshiProjects")
        folder_path = QFileDialog.getExistingDirectory(self, "Select Project Folder", default_path)
        if folder_path:
            project_name = os.path.basename(folder_path)
            project_manager = ProjectManager()
            project_manager.add_project(project_name, folder_path)
            print(f"Selected folder: {folder_path}")
            self.close()
            from teshi.views.main_window import MainWindow
            main_window = MainWindow(project_name, folder_path)
            main_window.show()
            
    def open_project(self, path):
        """
        Open a project from the given path and close the current window.
        
        Args:
            path (str): The path of the project to open.
        """
        from teshi.views.main_window import MainWindow
        from PySide6.QtCore import Qt
        project_name = os.path.basename(path)
        # Save as member variable
        self.main_window = MainWindow(project_name, path)
        # Prevent deletion on close
        self.main_window.setAttribute(Qt.WA_DeleteOnClose, False)
        self.main_window.show()

        # Update current project in project manager
        project_manager = ProjectManager()
        project_manager.update_projects(path)


        # Ensure the new window is fully displayed before closing the current window
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.close() if self.isVisible() else None)

