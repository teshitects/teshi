from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QMenuBar, QMenu
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon


class MainWindow(QMainWindow):
    def __init__(self, project_name, project_path):
        super().__init__()
        self.project_name = project_name
        self.project_path = project_path
        self.setWindowTitle(f"{project_name} - Teshi - {project_path}")
        self.setWindowIcon(QIcon("assets/teshi_icon64.png"))
        self.setGeometry(100, 100, 1200, 800)
        self._setup_menubar()
        self._setup_layout()

    def _setup_menubar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")
        import_action = QAction("Import Test Cases", self)
        file_menu.addAction(import_action)
        import_action.triggered.connect(self._import_test_cases)

        # Help Menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        help_menu.addAction(about_action)
        about_action.triggered.connect(self._show_about_dialog)

    def _show_about_dialog(self):
        from teshi.views.widgets.about_dialog import AboutDialog
        about_dialog = AboutDialog()
        about_dialog.exec()

    def _import_test_cases(self):
        from PySide6.QtWidgets import QFileDialog
        # file_path, _ = QFileDialog.getOpenFileName(self, "Open Test Case File", "", "JSON Files (*.json);;All Files (*)")

        # from teshi.views.widgets.import_testcase_wizard_dialog import TestcaseImportDialog
        # import_dialog = TestcaseImportDialog(self)
        # import_dialog.exec()

    def _setup_layout(self):
        # Main Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main Layout (Horizontal)
        main_layout = QHBoxLayout(main_widget)

        # Left Panel (Project Navigation)
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: #2b2b2b; color: white;")
        left_layout = QVBoxLayout(left_panel)
        left_label = QLabel("Project Navigation")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-size: 12pt;")
        left_layout.addWidget(left_label)

        # Test Cases Section
        test_cases_label = QLabel("Test Cases")
        test_cases_label.setAlignment(Qt.AlignCenter)
        test_cases_label.setStyleSheet("font-size: 12pt;")
        left_layout.addWidget(test_cases_label)


        main_layout.addWidget(left_panel, stretch=1)

        # Right Splitter (Vertical)
        right_splitter = QSplitter(Qt.Vertical)

        # Editor Panel
        editor_panel = QWidget()
        editor_panel.setStyleSheet("background-color: #1e1e1e; color: white;")
        editor_layout = QVBoxLayout(editor_panel)
        editor_label = QLabel("Editor")
        editor_label.setAlignment(Qt.AlignCenter)
        editor_label.setStyleSheet("font-size: 12pt;")
        editor_layout.addWidget(editor_label)
        right_splitter.addWidget(editor_panel)

        # Terminal Panel
        terminal_panel = QWidget()
        terminal_panel.setStyleSheet("background-color: #1e1e1e; color: white;")
        terminal_layout = QVBoxLayout(terminal_panel)
        terminal_label = QLabel("Terminal")
        terminal_label.setAlignment(Qt.AlignCenter)
        terminal_label.setStyleSheet("font-size: 12pt;")
        terminal_layout.addWidget(terminal_label)
        right_splitter.addWidget(terminal_panel)

        main_layout.addWidget(right_splitter, stretch=4)

