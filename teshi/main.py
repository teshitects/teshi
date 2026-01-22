import sys
import os

# Add application path to sys.path,
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    application_path = sys._MEIPASS
else:
    # Running in normal Python environment
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Insert the application path at the start of sys.path
sys.path.insert(0, application_path)

from PySide6.QtWidgets import QApplication
from teshi.views.project_select_page import ProjectSelectPage

if __name__ == "__main__":
    app = QApplication(sys.argv)
    project_select_page = ProjectSelectPage()
    project_select_page.show()
    sys.exit(app.exec())