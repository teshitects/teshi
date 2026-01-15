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
                    item.remove()
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
        # Unique title check or suffix if needed?
        # For now, simplistic approach:
        # If title exists, we might want to append a number, but right_click_add_node logic 
        # usually handles unique titles (User adds timestamp).
        # But here we are dragging a "Template".
        # Let's verify uniqueness or append suffix.
        
        final_title = title
        existing_titles = [item.data_model.title for item in self._scene.items() if isinstance(item, JupyterGraphNode)]
        if final_title in existing_titles:
            # Append suffix
            i = 1
            while f"{title}_{i}" in existing_titles:
                i += 1
            final_title = f"{title}_{i}"
            
        item = JupyterGraphNode(final_title, code)
        if self.father is not None:
            item.signals.nodeClicked.connect(self.father.update_widget)
        self._scene.addItem(item)
        item.setPos(mouse_pos)
        item.data_model.x = mouse_pos.x()
        item.data_model.y = mouse_pos.y()
        
        # Trigger update of input widgets immediately just in case
        # (Already called in __init__ of JupyterGraphNode)

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
        
        # Determine base name without existing numeric suffix if it looks like a copy?
        # Or just append _copy or number.
        # Requirement: "The created node... is equivalent to a copy" 
        # Usually copies have new names to be unique in graph if titles must be unique.
        # Assuming titles must be unique.
        
        i = 1
        while final_title in existing_titles:
            final_title = f"{base_title}_{i}"
            i += 1
            
        # Create new node with same code
        new_node = JupyterGraphNode(final_title, source_node.data_model.code)
        
        # Copy params
        # IMPORTANT: We must deep copy params to avoid shared state if params are mutable objects
        import copy
        new_node.data_model.params = copy.deepcopy(source_node.data_model.params)
        
        # Refresh inputs to reflect copied params
        new_node.update_input_widgets()
        
        if self.father is not None:
            new_node.signals.nodeClicked.connect(self.father.update_widget)
            
        self._scene.addItem(new_node)
        new_node.setPos(mouse_pos)
        new_node.data_model.x = mouse_pos.x()
        new_node.data_model.y = mouse_pos.y()


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
            self.right_click_add_node(f"# Node {get_timestamp_str_millisecond()}", self.mapToScene(event.pos()))
        return super().mousePressEvent(event)



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

    def right_click_add_node(self, title, mouse_pos):
        item = JupyterGraphNode(title, title)
        # add click event
        father = self.father
        if self.father is not None:
            item.signals.nodeClicked.connect(self.father.update_widget)
        self._scene.addItem(item)
        item.setPos(mouse_pos)
        item.data_model.x = mouse_pos.x()
        item.data_model.y = mouse_pos.y()

