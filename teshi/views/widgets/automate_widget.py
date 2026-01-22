from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QTransform
from PySide6.QtCore import Qt, QLine, QEvent, QLineF
from teshi.config.automate_editor_config import *
from teshi.utils.time_util import get_timestamp_str_millisecond
from teshi.views.widgets.component.automate_connection_item import ConnectionItem
import PySide6
import math

from teshi.views.widgets.graph_node import JupyterGraphNode


class NodeSketchpadScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setBackgroundBrush(QBrush(QColor(AutomateEditorConfig.scene_background_color)))

        self._width = AutomateEditorConfig.scene_width
        self._height = AutomateEditorConfig.scene_height
        # Center the scene
        self.setSceneRect(
            -self._width / 2, -self._height / 2, self._width, self._height
        )

        self._grid_size = AutomateEditorConfig.scene_grid_size
        self._grid_chunk = AutomateEditorConfig.scene_grid_chunk

        self._normal_line_pen = QPen(
            QColor(AutomateEditorConfig.scene_grid_normal_line_color)
        )
        self._normal_line_pen.setWidthF(AutomateEditorConfig.scene_grid_normal_line_width)

        self._dark_line_pen = QPen(QColor(AutomateEditorConfig.scene_grid_dark_line_color))
        self._dark_line_pen.setWidthF(AutomateEditorConfig.scene_grid_dark_line_width)


    def addItem(self, item):
        super().addItem(item)

    def drawBackground(self, painter: PySide6.QtGui.QPainter, rect):
        super().drawBackground(painter, rect)

        lines, dark_lines = self.cal_grid_lines(rect)
        painter.setPen(self._dark_line_pen)
        painter.drawLines(dark_lines)
        painter.setPen(self._normal_line_pen)
        painter.drawLines(lines)

    def cal_grid_lines(self, rect):
        left, right, top, bottom = (
            math.floor(rect.left()),
            math.floor(rect.right()),
            math.floor(rect.top()),
            math.floor(rect.bottom()),
        )

        # Top left corner
        first_left = left - (left % self._grid_size)
        first_top = top - (top % self._grid_size)

        # Calculate the start and end points of the lines
        lines = []
        dark_lines = []
        # Draw horizontal lines
        for v in range(first_top, bottom, self._grid_size):
            line = QLine(left, v, right, v)
            if v % (self._grid_size * self._grid_chunk) == 0:
                dark_lines.append(line)
            else:
                lines.append(line)
        # Draw vertical lines
        for h in range(first_left, right, self._grid_size):
            line = QLine(h, top, h, bottom)
            if h % (self._grid_size * self._grid_chunk) == 0:
                dark_lines.append(line)
            else:
                lines.append(line)

        return lines, dark_lines
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for item in self.selectedItems():
                if isinstance(item, ConnectionItem):
                    item._disconnect()
                elif isinstance(item,JupyterGraphNode):
                    # Delegate removal to controller if possible
                    if self.parent() and hasattr(self.parent(), 'controller'):
                        self.parent().controller.remove_node(item.data_model.uuid)
                    else:
                        item.remove() # Fallback
        super().keyPressEvent(event)

class NodeSketchpadView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.father = parent

        self._scene = scene
        self.setScene(self._scene)

        # Make the animation more smooth
        self.setRenderHint(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        # Hide the scrollbar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Always track the mouse when adjust the ratio
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        #
        self._drag_mode = False
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-teshi-node"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-teshi-node"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-teshi-node"):
            import json
            data = event.mimeData().data("application/x-teshi-node")
            node_data = json.loads(data.data().decode('utf-8'))
            
            mouse_pos = self.mapToScene(event.pos())
            
            if node_data["type"] == "new_node":
                title = node_data["title"]
                code = node_data["code"]
                self.add_node_on_drop(title, code, mouse_pos)
            elif node_data["type"] == "copy_node":
                source_title = node_data["title"]
                self.copy_node_on_drop(source_title, mouse_pos)
                
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def add_node_on_drop(self, title, code, mouse_pos):
        # Calculate unique title
        final_title = title
        existing_titles = [item.data_model.title for item in self._scene.items() if isinstance(item, JupyterGraphNode)]
        if final_title in existing_titles:
            i = 1
            while f"{title}_{i}" in existing_titles:
                i += 1
            final_title = f"{title}_{i}"
            
        if self.father and hasattr(self.father, 'controller'):
            self.father.controller.add_node(final_title, code, (mouse_pos.x(), mouse_pos.y()))

    def copy_node_on_drop(self, source_title, mouse_pos):
        # Find source node
        source_node = None
        for item in self._scene.items():
            if isinstance(item, JupyterGraphNode) and item.data_model.title == source_title:
                source_node = item
                break
        
        if not source_node:
            print(f"Source node {source_title} not found for copy.")
            return

        # Prepare new title
        base_title = source_node.data_model.title
        final_title = base_title
        existing_titles = [item.data_model.title for item in self._scene.items() if isinstance(item, JupyterGraphNode)]
        
        i = 1
        while final_title in existing_titles:
            final_title = f"{base_title}_{i}"
            i += 1
            
        # Copy params
        import copy
        params = copy.deepcopy(source_node.data_model.params)
        
        if self.father and hasattr(self.father, 'controller'):
            self.father.controller.add_node(final_title, source_node.data_model.code, (mouse_pos.x(), mouse_pos.y()), params=params)


    def wheelEvent(self, event):
        # Zoom
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        # When no node is selected, the entire canvas can be dragged
        if event.button() == Qt.LeftButton:
            self.leftButtonPressed(event)
        if event.button() == Qt.RightButton:
            self.show_context_menu(event)
        return super().mousePressEvent(event)

    def show_context_menu(self, event):
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self)
        
        action_raw = QAction("Add Raw Node", self)
        action_raw.triggered.connect(lambda: self.right_click_add_node(f"Node {get_timestamp_str_millisecond()}", self.mapToScene(event.pos()), "raw"))
        menu.addAction(action_raw)
        
        action_api = QAction("Add API Node", self)
        action_api.triggered.connect(lambda: self.right_click_add_node(f"API {get_timestamp_str_millisecond()}", self.mapToScene(event.pos()), "api"))
        menu.addAction(action_api)
        
        action_ui = QAction("Add UI Node", self)
        action_ui.triggered.connect(lambda: self.right_click_add_node(f"UI {get_timestamp_str_millisecond()}", self.mapToScene(event.pos()), "ui"))
        menu.addAction(action_ui)
        
        action_mobile_ui = QAction("Add Mobile UI Node", self)
        action_mobile_ui.triggered.connect(lambda: self.right_click_add_node(f"Mobile {get_timestamp_str_millisecond()}", self.mapToScene(event.pos()), "mobile_ui"))
        menu.addAction(action_mobile_ui)

        menu.exec_(event.globalPos())



        self._drag_mode = None
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            self.leftButtonReleased(event)
        return super().mouseReleaseEvent(event)

    def leftButtonPressed(self, event):
        if self.itemAt(event.pos()) is not None:
            return
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._drag_mode = True

    def leftButtonReleased(self, event):
        self.setDragMode(QGraphicsView.NoDrag)
        self._drag_mode = False

    def right_click_add_node(self, title, mouse_pos, node_type="raw"):
        if self.father and hasattr(self.father, 'controller'):
            self.father.controller.add_node(title, title if node_type=="raw" else "", (mouse_pos.x(), mouse_pos.y()), node_type=node_type)

