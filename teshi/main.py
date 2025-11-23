import sys

from PySide6.QtWidgets import QApplication

from teshi.views.project_select_page import ProjectSelectPage

if __name__ == "__main__":
    app = QApplication(sys.argv)
    project_select_page = ProjectSelectPage()
    project_select_page.show()
    sys.exit(app.exec())