from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsLineItem, QMessageBox, QGraphicsProxyWidget, QLineEdit, QComboBox, QSpinBox, QLabel, QWidget, QVBoxLayout
from PySide6.QtGui import QBrush, QPen, QColor, QPolygonF, QPainterPath, QFont, QTransform
from PySide6.QtCore import Qt, QRectF, QLineF, Signal
import uuid
import ast
from teshi.config.automate_editor_config import AutomateEditorConfig
from teshi.views.widgets.component.automate_connection_item import ConnectionItem
from teshi.views.widgets.component.item_signals import ItemSignals
from teshi.models.jupyter_node_model import JupyterNodeModel



class JupyterGraphNode(QGraphicsItem):
    clicked = Signal(dict)

    def __init__(self, title, code, parent=None):
        super().__init__(parent)
        self.data_model = JupyterNodeModel(title, code)
        if self.data_model.uuid is None:
            self.data_model.uuid = str(uuid.uuid4())

        self.signals = ItemSignals()

        self._node_width = AutomateEditorConfig.node_width
        self._node_height = AutomateEditorConfig.node_height
        self._node_radius = AutomateEditorConfig.node_radius
        self._inputs_height = 0
        self.observers = []

        # Create Node pen and brush
        self._pen =  AutomateEditorConfig.node_default_pen
        self._selected_pen = AutomateEditorConfig.node_selected_pen
        self._background_color = AutomateEditorConfig.node_background_color
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)

        # Create title
        self._title = title
        self._title_color = AutomateEditorConfig.node_title_color
        self._title_font = AutomateEditorConfig.node_title_font
        self._title_height = AutomateEditorConfig.node_title_height
        self._title_padding = AutomateEditorConfig.node_title_padding
        self._title_brush_back = AutomateEditorConfig.node_title_brush_back
        self.init_title()

        # Create result text
        self._result_text = ""
        self._result_text_color = AutomateEditorConfig.node_title_color
        self._result_text_font = AutomateEditorConfig.node_title_font
        self._result_text_height = AutomateEditorConfig.node_title_height
        self._result_text_padding = AutomateEditorConfig.node_title_padding
        self.init_result_text()

        self.drag_mode = None  # 'move' or 'connect'
        self.temp_connection = None
        self.connections = []

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        
        # Dynamic inputs
        self.input_proxies = {} # map label -> proxy widget
        self.update_input_widgets()
    
    def parse_inputs_from_code(self):
        inputs = []
        try:
            tree = ast.parse(self.data_model.code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'user_input':
                    # Extract args
                    args = [getattr(arg, 'value', None) for arg in node.args]
                    kwargs = {kw.arg: getattr(kw.value, 'value', None) for kw in node.keywords}
                    # Also handle list/dict in kwargs if possible (e.g. options=['A', 'B'])
                    # AST for list is different: List(elts=[Constant(value='A'), ...])
                    for kw in node.keywords:
                        if kw.arg == 'options' and isinstance(kw.value, ast.List):
                             kwargs['options'] = [getattr(elt, 'value', str(elt)) for elt in kw.value.elts]

                    if len(args) > 0:
                        label = args[0]
                        default = args[1] if len(args) > 1 else None
                        input_type = kwargs.get('type', 'text')
                        options = kwargs.get('options', [])
                        inputs.append({
                            'label': label,
                            'default': default,
                            'type': input_type,
                            'options': options
                        })
        except Exception as e:
            print(f"Error parsing inputs: {e}")
        return inputs

    def update_input_widgets(self):
        input_defs = self.parse_inputs_from_code()
        current_labels = set(self.input_proxies.keys())
        new_labels = set(d['label'] for d in input_defs)
        
        # Remove old
        for label in current_labels - new_labels:
            proxy = self.input_proxies.pop(label)
            self.scene().removeItem(proxy) if self.scene() else None
            proxy.setWidget(None) # release widget

        # Add/Update new
        y_offset = self._title_height + self._title_padding + 10
        
        for def_data in input_defs:
            label = def_data['label']
            if label not in self.input_proxies:
                # Create widget container
                container = QWidget()
                layout = QVBoxLayout(container)
                layout.setContentsMargins(0,0,0,0)
                layout.setSpacing(2)
                
                lbl = QLabel(label)
                lbl.setStyleSheet("color: white; font-size: 10px;")
                layout.addWidget(lbl)
                
                if def_data['type'] == 'select':
                    widget = QComboBox()
                    widget.addItems(def_data.get('options', []))
                    current_val = self.data_model.params.get(label, def_data['default'])
                    widget.setCurrentText(str(current_val))
                    widget.currentTextChanged.connect(lambda val, l=label: self.on_param_changed(l, val))
                elif def_data['type'] == 'number':
                    widget = QSpinBox()
                    widget.setValue(int(self.data_model.params.get(label, def_data.get('default', 0))))
                    widget.valueChanged.connect(lambda val, l=label: self.on_param_changed(l, val))
                else: # text
                    widget = QLineEdit()
                    widget.setText(str(self.data_model.params.get(label, def_data.get('default', ''))))
                    widget.textChanged.connect(lambda val, l=label: self.on_param_changed(l, val))
                
                layout.addWidget(widget)
                
                proxy = QGraphicsProxyWidget(self)
                proxy.setWidget(container)
                self.input_proxies[label] = proxy
            
            # Position the proxy
            proxy = self.input_proxies[label]
            proxy.setPos(-self._node_width/2 + 10, -self._node_height/2 + y_offset)
            proxy.setMinimumWidth(self._node_width - 20)
            proxy.setMaximumWidth(self._node_width - 20)
            y_offset += proxy.size().height() + 5
            
        # Adjust height? For now let's just let it overflow or expand rect if needed
        # We need to update result text position
        self._inputs_height = y_offset - (self._title_height + self._title_padding + 10)
        if hasattr(self, '_result_textitem'):
             self._result_textitem.setPos(-self._node_width / 2 + self._result_text_padding, 
                                          -self._node_height / 2 + self._title_height + self._inputs_height + 20)

    def on_param_changed(self, label, value):
        self.data_model.params[label] = value

    def to_dict(self):
        # Update params from widgets just in case? No, signals handle it.
        return super().to_dict()

    def remove_connection(self, connection):
        if connection in self.connections:
            self.connections.remove(connection)
            self.data_model.children.remove(connection.destination.data_model.title)

    def add_connection(self, connection):
        self.connections.append(connection)

    def addObserver(self, observer):
        self.observers.append(observer)

    def itemChange(self, change, value):
        """ ItemChange EventHandle"""
        if change == QGraphicsItem.ItemPositionHasChanged:
            for observer in self.observers:
                observer.update()
        return super().itemChange(change, value)

    def boundingRect(self):
        height = self._node_height + self._inputs_height
        return QRectF(-self._node_width / 2, -self._node_height / 2, self._node_width, height)
        # return self.shape().boundingRect()

    def paint(self, painter, option, widget):
        height = self._node_height + self._inputs_height
        node_outline = QPainterPath()
        node_outline.addRoundedRect(-self._node_width / 2, -self._node_height / 2, self._node_width, height, self._node_radius, self._node_radius)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._background_color)
        painter.drawPath(node_outline)

        # Draw title
        title_outline = QPainterPath()
        title_outline.setFillRule(Qt.WindingFill)
        title_outline.addRoundedRect(-self._node_width / 2, -self._node_height / 2, self._node_width, self._title_height, self._node_radius, self._node_radius)

        # Draw a small filled rectangle at the lower left and lower right corners of the title.
        title_outline.addRect(-self._node_width / 2 + self._node_width-self._node_radius , -self._node_height / 2 + self._title_height - self._node_radius, self._node_radius, self._node_radius)
        title_outline.addRect(-self._node_width / 2 , -self._node_height / 2 + self._title_height - self._node_radius, self._node_radius, self._node_radius)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._title_brush_back)
        painter.drawPath(title_outline)

        if self.isSelected():
            painter.setPen(self._selected_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(node_outline)
        else:
            painter.setPen(self._pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(node_outline)


    def init_title(self):
        self._titleitem = QGraphicsTextItem(self)
        self._titleitem.setPlainText(self._title)
        self._titleitem.setFont(self._title_font)
        self._titleitem.setDefaultTextColor(self._title_color)
        self._titleitem.setPos(-self._node_width / 2 + self._title_padding, -self._node_height / 2 + self._title_padding)

    def mousePressEvent(self, event):
        # Differentiate between modes using the Ctrl key
        if event.modifiers() == Qt.ControlModifier:
            # Connect mode: Start creating a temporary line
            self.drag_mode = 'connect'
            self.temp_connection = QGraphicsLineItem(
                QLineF(self.sceneBoundingRect().center(), event.scenePos()))
            self.temp_connection.setPen(QPen(Qt.white, 2, Qt.DashLine))

            self.scene().addItem(self.temp_connection)
        else:
            if event.button() == Qt.LeftButton:
                # Select node
                self.signals.nodeClicked.emit(self.to_dict())
                event.accept()
            # Move mode: Handled by the parent class
            self.drag_mode = 'move'
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_mode == 'connect':
            # Update temporary connection line
            start = self.sceneBoundingRect().center()
            self.temp_connection.setLine(QLineF(start, event.scenePos()))
        else:
            # Normal move node
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag_mode == 'connect':
            # Complete the connection creation
            self.scene().removeItem(self.temp_connection)
            self.temp_connection = None

            # Detection target item
            target_item = self.scene().itemAt(event.scenePos(), QTransform())
            if (isinstance(target_item, JupyterGraphNode) and
                    target_item != self):
                connection = ConnectionItem(self, target_item)
                self.scene().addItem(connection)
                self.connections.append(connection)
                target_item.connections.append(connection)


        self.drag_mode = None
        super().mouseReleaseEvent(event)

    def to_dict(self):
        self.data_model.title = self._title
        self.data_model.x  = self.pos().x()
        self.data_model.y  = self.pos().y()
        return self.data_model.to_dict()

    def set_color(self, color):
        # self._pen.setColor(color)
        # set node background color
        self._background_color = color

        self.update()

    def set_default_color(self):
        self._background_color = AutomateEditorConfig.node_background_color
        self.update()

    def init_result_text(self):
        self._result_textitem = QGraphicsTextItem(self)
        self._result_textitem.setPlainText(self._result_text)
        self._result_textitem.setFont(self._result_text_font)
        self._result_textitem.setDefaultTextColor(self._result_text_color)
        self._result_textitem.setPos(-self._node_width / 2 + self._result_text_padding, -self._node_height / 2 + self._result_text_padding + self._title_height + self._title_padding)

    def set_result_text(self, text):
        self._result_text = text
        self._result_textitem.setPlainText(self._result_text)
        self._result_textitem.update()

    def set_title_text(self, text):
        self._title = text
        self._titleitem.setPlainText(self._title)
        self._titleitem.update()

    def remove(self):
        confirm = QMessageBox.question(
            None, "Delete Node", "Are you sure you want to delete this node and all its connections?？",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        for conn in self.connections.copy():
            conn._disconnect()

        if self.scene():
            self.scene().removeItem(self)

    def set_default_text(self):
        self._result_text = ""
        self._result_textitem.setPlainText(self._result_text)
        self._result_textitem.update()

