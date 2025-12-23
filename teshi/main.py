import sys
import os

# 添加项目根目录到 Python 路径（用于 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    # 运行在打包后的 exe 中
    application_path = sys._MEIPASS
else:
    # 运行在正常 Python 环境中
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, application_path)

from PySide6.QtWidgets import QApplication
from teshi.views.project_select_page import ProjectSelectPage

if __name__ == "__main__":
    app = QApplication(sys.argv)
    project_select_page = ProjectSelectPage()
    project_select_page.show()
    sys.exit(app.exec())