from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QBrush, QColor, QPen


class AutomateEditorConfig:
    scene_width = 32000
    scene_height = 32000

    scene_background_color = "#212121"

    # Drawing grid in the editor
    scene_grid_normal_line_color = "#313131"
    scene_grid_dark_line_color = "#131313"
    scene_grid_normal_line_width = 1.0
    scene_grid_dark_line_width = 1.0
    # width
    scene_grid_size = 20
    # Determine how many small cells there are in the big cell
    scene_grid_chunk = 5

    # Graph node
    node_width = 160
    node_height = 80
    node_radius = 10
    node_default_pen = QPen(QColor("#151515"))
    node_selected_pen = QPen(QColor("#aaffee00"))
    node_background_color = QBrush(QColor("#151515"))

    # Node title
    node_title_height = 30
    node_title_padding = 3
    node_title_font = QFont('Consolas', 13)
    node_title_color = Qt.white
    node_title_brush_back = QBrush(QColor("#aa00003f"))

    # Connection
    connection_line_color = QColor("#aaababab")
    connection_line_arrow_size = 20
    connection_line_arrow_color = connection_line_color
    connection_line_selected_color = QColor("#aaffee00")