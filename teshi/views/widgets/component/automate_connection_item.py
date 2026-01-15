import math

from PySide6.QtCore import QRectF, QLineF, QPointF, Qt
from PySide6.QtGui import QPolygonF, QColor
from PySide6.QtWidgets import QGraphicsItem

from teshi.config.automate_editor_config import AutomateEditorConfig


class ConnectionItem(QGraphicsItem):
    def __init__(self, source: 'JupyterGraphNode', destination: 'JupyterGraphNode'):
        super().__init__()
        self.source = source
        self.destination = destination
        self.source.data_model.children.append(self.destination.data_model.title)

        self.setZValue(-1)

        # Listen for changes in the position of the source and target
        self.source.addObserver(self)
        self.destination.addObserver(self)
        self.setFlag(QGraphicsItem.ItemIsSelectable)  # 允许选中
        self.setFlag(QGraphicsItem.ItemIsFocusable)    # 接收键盘事件

    def _disconnect(self):
        # 通知节点移除连接
        self.source.remove_connection(self)
        self.destination.remove_connection(self)
        # 从场景中移除自身
        if self.scene():
            self.scene().removeItem(self)

    def addObserver(self, item):
        item.installSceneEventFilter(self)

    def sceneEventFilter(self, watched, event):
        # Update connection lines when source or target moves
        if watched in (self.source, self.destination) and event.type() == event.GraphicsItemMove:
            self.update()
        return super().sceneEventFilter(watched, event)

    def boundingRect(self):
        # Compute bounding box, including lines and arrows
        start = self.source.sceneBoundingRect().center()
        end = self.destination.sceneBoundingRect().center()
        return QRectF(start, end).normalized().adjusted(-10, -10, 10, 10)

    def paint(self, painter, option, widget):
        # Get the actual coordinates in the scene
        start_point = self.source.sceneBoundingRect().center()
        end_point = self.destination.sceneBoundingRect().center()

        # Draw a connection line
        line = QLineF(start_point, end_point)
        painter.setPen(AutomateEditorConfig.connection_line_color)
        painter.drawLine(line)

        center_point = line.center()

        # Calculate arrow angle and position
        angle = math.atan2(-line.dy(), line.dx())
        arrow_size = AutomateEditorConfig.connection_line_arrow_size
        arrow_p1 = center_point + QPointF(
            math.sin(angle - math.pi / 3) * arrow_size,
            math.cos(angle - math.pi / 3) * arrow_size
        )
        arrow_p2 = center_point + QPointF(
            math.sin(angle - math.pi * 2 / 3) * arrow_size,
            math.cos(angle - math.pi * 2 / 3) * arrow_size
        )

        # Draw arrow
        arrow_head = QPolygonF()
        arrow_head.append(center_point)
        arrow_head.append(arrow_p1)
        arrow_head.append(arrow_p2)
        painter.setBrush(AutomateEditorConfig.connection_line_arrow_color)
        painter.drawPolygon(arrow_head)

        if self.isSelected():
            painter.setPen(AutomateEditorConfig.connection_line_selected_color)
            painter.drawLine(line)
            painter.drawPolygon(arrow_head)
        else:
            painter.setPen(AutomateEditorConfig.connection_line_color)
            painter.drawLine(line)
            painter.drawPolygon(arrow_head)
