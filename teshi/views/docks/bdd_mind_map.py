import json
import re
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView,
                               QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem,
                               QGraphicsLineItem, QGraphicsTextItem, QPushButton,
                               QToolBar, QSlider, QLabel, QFrame, QScrollArea,
                               QGraphicsRectItem, QComboBox, QCheckBox)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QWheelEvent, QRadialGradient

from teshi.utils.bdd_converter import BDDConverter
from teshi.utils.keyword_highlighter import KeywordHighlighter


class BDDNodeItem(QGraphicsEllipseItem):
    """BDD node graphics item"""

    def __init__(self, node_type: str, title: str, content: str = "", x: float = 0, y: float = 0, parent=None):
        self.node_type = node_type  # 'scenario', 'given', 'when', 'then', 'notes'
        self.title = title
        self.content = content
        self.radius = 40 if node_type == 'scenario' else 30

        super().__init__(-self.radius / 2, -self.radius / 2, self.radius, self.radius, parent)

        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        # Set color
        self._setup_colors()

        # Set text
        self.text_item = QGraphicsTextItem(self.title, self)
        self.text_item.setDefaultTextColor(Qt.white)
        font = QFont("Arial", 8)
        self.text_item.setFont(font)
        self.text_item.setPos(-self.radius / 2 + 5, -self.radius / 2 + 5)

        # Set tooltip
        tooltip_text = f"{self.node_type.upper()}: {self.title}"
        if self.content:
            tooltip_text += f"\n{self.content}"
        self.setToolTip(tooltip_text)

        # Connection items
        self.connections = []

    def _setup_colors(self):
        """Set node color - 与左侧BDD视图保持一致"""
        colors = {
            'scenario': QColor(96, 125, 139),  # Blue Grey #607D8B - 场景节点用灰蓝色,更沉稳
            'given': QColor(76, 175, 80),  # Green #4CAF50 - 与BDD视图一致
            'when': QColor(255, 152, 0),  # Orange #FF9800 - 与BDD视图一致
            'then': QColor(33, 150, 243),  # Blue #2196F3 - 与BDD视图一致
            'notes': QColor(156, 39, 176)  # Purple #9C27B0 - 与BDD视图一致
        }

        color = colors.get(self.node_type, QColor(149, 165, 166))
        self.setBrush(QBrush(color))
        # 移除边框,避免遮挡文字
        self.setPen(QPen(Qt.NoPen))

    def itemChange(self, change, value):
        """Handle item changes and update connections"""
        if change == QGraphicsItem.ItemPositionHasChanged:
            for connection in self.connections:
                connection.update_position()
        return super().itemChange(change, value)

    def add_connection(self, connection):
        """Add a connection line"""
        self.connections.append(connection)


class BDDConnectionItem(QGraphicsLineItem):
    """BDD node connection line"""

    def __init__(self, start_node: BDDNodeItem, end_node: BDDNodeItem, parent=None):
        self.start_node = start_node
        self.end_node = end_node

        super().__init__(parent)

        # 更轻盈的连接线样式:虚线、更细、更透明
        pen = QPen(QColor(150, 150, 150, 80), 1, Qt.DashLine)
        pen.setDashPattern([3, 3])  # 虚线模式
        self.setPen(pen)
        
        # 设置层级,让连接线在节点下方
        self.setZValue(-1)

        start_node.add_connection(self)
        end_node.add_connection(self)

        self.update_position()

    def update_position(self):
        """Update connection line position"""
        start_pos = self.start_node.scenePos()
        end_pos = self.end_node.scenePos()

        self.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())


class BDDMindMapView(QGraphicsView):
    """BDD mind map view"""

    node_clicked = Signal(str, dict)  # Node click signal (node_type, node_data)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)  # Set a large scene area for panning
        self.setScene(self.scene)

        # Setup view properties
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Node storage
        self.nodes = {}
        self.connections = []

        # Layout parameters - 更紧凑的布局
        self.level_height = 80  # 垂直间距
        self.node_spacing = 120  # 水平间距
        
        # Initialize keyword highlighter
        self.keyword_highlighter = KeywordHighlighter()

        # Zoom control
        self._scale_factor = 1.0
        self._min_scale = 0.3
        self._max_scale = 3.0
        
        # Dragging control
        self._is_panning = False
        self._last_pan_point = None

    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            # Check if clicking on an item
            item = self.itemAt(event.pos())
            if item is None:
                # Start panning if not clicking on an item
                self._is_panning = True
                self._last_pan_point = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move event"""
        if self._is_panning and self._last_pan_point is not None:
            # Calculate movement delta in view coordinates
            delta = event.pos() - self._last_pan_point
            self._last_pan_point = event.pos()
            
            # Adjust the scrollbars to move the view
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release event"""
        if event.button() == Qt.LeftButton and self._is_panning:
            self._is_panning = False
            self._last_pan_point = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        """Mouse wheel zoom"""
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        # Save original scene position
        old_pos = self.mapToScene(event.position().toPoint())

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        if self._min_scale < self._scale_factor * zoom_factor < self._max_scale:
            self.scale(zoom_factor, zoom_factor)
            self._scale_factor *= zoom_factor

        # Get new position
        new_pos = self.mapToScene(event.position().toPoint())

        # Adjust scene position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def clear_graph(self):
        """Clear graphics with proper memory cleanup"""
        # Close all items in the scene
        self.scene.clear()
        
        # Clear references
        self.nodes.clear()
        self.connections.clear()
    
    # Keyword highlighting methods
    def set_highlight_keywords(self, keywords: list):
        """Set the list of keywords to highlight"""
        self.keyword_highlighter.set_keywords(keywords)
        self._apply_keyword_highlighting()
    
    def add_highlight_keyword(self, keyword: str):
        """Add a single keyword for highlighting"""
        self.keyword_highlighter.add_keyword(keyword)
        self._apply_keyword_highlighting()
    
    def remove_highlight_keyword(self, keyword: str):
        """Remove keyword highlighting"""
        self.keyword_highlighter.remove_keyword(keyword)
        self._apply_keyword_highlighting()
    
    def clear_highlight_keywords(self):
        """Clear all keyword highlighting"""
        self.keyword_highlighter.clear_keywords()
        self._apply_keyword_highlighting()
    
    def set_highlight_color(self, color):
        """Set highlight color"""
        self.keyword_highlighter.set_highlight_color(color)
        self._apply_keyword_highlighting()
    
    def get_highlight_keywords(self) -> list:
        """Get the current list of keywords"""
        return self.keyword_highlighter.keywords.copy()
    
    def _apply_keyword_highlighting(self):
        """Apply keyword highlighting in the mind map"""
        if not self.keyword_highlighter.keywords:
            # Clear all highlighting, restore default style
            self._clear_node_highlighting()
            return
        
        print(f"Applying keyword highlighting for keywords: {self.keyword_highlighter.keywords}")
        print(f"Total nodes to process: {len(self.nodes)}")
        
        if len(self.nodes) == 0:
            print("No nodes in mind map - nothing to highlight")
            return
        
        # Iterate through all nodes, apply highlighting
        for node_id, node in self.nodes.items():
            self._apply_node_highlighting(node)
    
    def _clear_node_highlighting(self):
        """Clear all node highlighting"""
        for node_id, node in list(self.nodes.items()):  # Use list() to avoid modification during iteration
            # Check if node and its text_item are still valid
            if node and hasattr(node, 'text_item') and node.text_item:
                try:
                    # Restore default style
                    self._set_node_default_style(node)
                except RuntimeError as e:
                    # Object already deleted, remove from nodes dict
                    if "already deleted" in str(e):
                        self.nodes.pop(node_id, None)
                    continue
                except:
                    # Other errors, skip this node
                    continue
    
    def _apply_node_highlighting(self, node):
        """Apply keyword highlighting to a single node"""
        if not isinstance(node, BDDNodeItem):
            return
        
        # Check if node and its text_item are still valid
        if not node or not hasattr(node, 'text_item') or not node.text_item:
            return
            
        try:
            node_title = node.title
            node_content = node.content
            
            # Check if title or content contains keywords
            text_to_check = f"{node_title} {node_content}"
            has_keyword = any(keyword.lower() in text_to_check.lower() for keyword in self.keyword_highlighter.keywords)
            
            print(f"Node '{node_title}' - has_keyword: {has_keyword}, checking in: '{text_to_check}'")
            
            if has_keyword:
                # Apply highlight style
                self._set_node_highlight_style(node)
                print(f"Applied highlight style to node '{node_title}'")
            else:
                # Restore default style
                self._set_node_default_style(node)
        except RuntimeError as e:
            # Object already deleted
            if "already deleted" in str(e):
                print(f"Node object already deleted, skipping highlight")
            return
        except:
            # Other errors, skip this node
            return
    
    def _set_node_default_style(self, node):
        """Set the default style for the node"""
        if not isinstance(node, BDDNodeItem):
            return
            
        # Check if node and text_item are still valid
        if not hasattr(node, 'text_item') or not node.text_item:
            return
            
        try:
            node_colors = {
                'scenario': QColor(76, 175, 80),      # Green
                'given': QColor(33, 150, 243),        # Blue  
                'when': QColor(255, 152, 0),         # Orange
                'then': QColor(156, 39, 176),        # Purple
                'notes': QColor(158, 158, 158)        # Gray
            }
            
            color = node_colors.get(node.node_type, QColor(100, 100, 100))
            
            # Set default colors and style
            node.setBrush(QBrush(color))
            node.setPen(QPen(QColor(255, 255, 255), 2))
            
            # Update text style - use plain text, not HTML
            node.text_item.setPlainText(node.title)  # Use plain text
            node.text_item.setDefaultTextColor(Qt.white)
            font = node.text_item.font()
            font.setBold(False)
            node.text_item.setFont(font)
        except RuntimeError as e:
            # Object already deleted
            if "already deleted" in str(e):
                print(f"Text item already deleted while setting default style")
            return
        except:
            # Other errors, skip this node
            return
    
    def _set_node_highlight_style(self, node):
        """Set the highlight style for the node text"""
        if not isinstance(node, BDDNodeItem):
            return
            
        # Check if node and text_item are still valid
        if not hasattr(node, 'text_item') or not node.text_item:
            return
            
        try:
            # Keep the node's default color style
            node_colors = {
                'scenario': QColor(76, 175, 80),      # Green
                'given': QColor(33, 150, 243),        # Blue  
                'when': QColor(255, 152, 0),         # Orange
                'then': QColor(156, 39, 176),        # Purple
                'notes': QColor(158, 158, 158)        # Gray
            }
            
            color = node_colors.get(node.node_type, QColor(100, 100, 100))
            node.setBrush(QBrush(color))
            node.setPen(QPen(QColor(255, 255, 255), 2))
            
            # Get highlight color
            bg_color = self.keyword_highlighter.highlight_format.background().color()
            fg_color = self.keyword_highlighter.highlight_format.foreground().color()
            
            # Update text style - by building rich text to highlight keywords
            original_text = node.title
            
            # Use HTML to build highlighted text
            highlighted_html = self._build_highlighted_html(original_text, bg_color, fg_color)
            node.text_item.setHtml(highlighted_html)
            
            font = node.text_item.font()
            font.setBold(True)  # Bold
            node.text_item.setFont(font)
        except RuntimeError as e:
            # Object already deleted
            if "already deleted" in str(e):
                print(f"Text item already deleted while setting highlight style")
            return
        except:
            # Other errors, skip this node
            return
    
    def _build_highlighted_html(self, text: str, bg_color: QColor, fg_color: QColor) -> str:
        """Build HTML text with highlighting"""
        if not self.keyword_highlighter.keywords:
            return f'<span style="color: white;">{text}</span>'
        
        # Highlight each keyword
        highlighted_text = text
        color_style = f'background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}); color: rgb({fg_color.red()}, {fg_color.green()}, {fg_color.blue()}); padding: 1px; border-radius: 2px; font-weight: bold;'
        
        for keyword in self.keyword_highlighter.keywords:
            import re
            # Use regex for case-insensitive replacement
            pattern = re.compile(f'({re.escape(keyword)})', re.IGNORECASE)
            replacement = f'<span style="{color_style}">\\1</span>'
            highlighted_text = pattern.sub(replacement, highlighted_text)
        
        return f'<span style="color: white;">{highlighted_text}</span>'

    def add_bdd_scenario(self, scenario_data: dict, scenario_index: int):
        """Add BDD scenario to the graph"""
        # Scenario node
        scenario_x = scenario_index * 400
        scenario_y = 0

        scenario_node = BDDNodeItem(
            'scenario',
            scenario_data['title'],
            scenario_data.get('notes', ''),
            scenario_x,
            scenario_y
        )
        self.scene.addItem(scenario_node)
        self.nodes[f'scenario_{scenario_index}'] = scenario_node

        # 采用三列错位布局,避免节点文字相互遮挡
        # 计算每列的起始Y位置(错开排列)
        base_y = scenario_y + self.level_height
        
        given_list = scenario_data.get('given', [])
        when_list = scenario_data.get('when', [])
        then_list = scenario_data.get('then', [])
        
        # 水平间距
        horizontal_spacing = 120
        # 垂直错位偏移量
        offset_step = self.level_height / 3  # 每列错开1/3行高
        
        # Given nodes - 左列 (基准位置)
        if given_list:
            given_x = scenario_x - horizontal_spacing
            given_offset = 0  # 左列不偏移
            for i, given in enumerate(given_list):
                given_content = given['content'] if isinstance(given, dict) else given
                given_y = base_y + given_offset + i * self.level_height
                given_node = BDDNodeItem('given', given_content, '', given_x, given_y)
                self.scene.addItem(given_node)
                self.nodes[f'given_{scenario_index}_{i}'] = given_node

                # Connect to scenario
                connection = BDDConnectionItem(scenario_node, given_node)
                self.scene.addItem(connection)
                self.connections.append(connection)

        # When nodes - 中列 (向下偏移)
        if when_list:
            when_x = scenario_x
            when_offset = offset_step  # 中列向下偏移1/3
            for i, when in enumerate(when_list):
                when_content = when['content'] if isinstance(when, dict) else when
                when_y = base_y + when_offset + i * self.level_height
                when_node = BDDNodeItem('when', when_content, '', when_x, when_y)
                self.scene.addItem(when_node)
                self.nodes[f'when_{scenario_index}_{i}'] = when_node

                # Connect to scenario
                connection = BDDConnectionItem(scenario_node, when_node)
                self.scene.addItem(connection)
                self.connections.append(connection)

        # Then nodes - 右列 (向下偏移更多)
        if then_list:
            then_x = scenario_x + horizontal_spacing
            then_offset = offset_step * 2  # 右列向下偏移2/3
            for i, then in enumerate(then_list):
                then_content = then['content'] if isinstance(then, dict) else then
                then_y = base_y + then_offset + i * self.level_height
                then_node = BDDNodeItem('then', then_content, '', then_x, then_y)
                self.scene.addItem(then_node)
                self.nodes[f'then_{scenario_index}_{i}'] = then_node

                # Connect to scenario
                connection = BDDConnectionItem(scenario_node, then_node)
                self.scene.addItem(connection)
                self.connections.append(connection)

        # Notes node - 放在scenario右上角
        if scenario_data.get('notes'):
            notes_x = scenario_x + horizontal_spacing * 1.5
            notes_y = scenario_y - 60
            notes_node = BDDNodeItem('notes', 'Notes', scenario_data['notes'], notes_x, notes_y)
            self.scene.addItem(notes_node)
            self.nodes[f'notes_{scenario_index}'] = notes_node

            # Connect to scenario
            connection = BDDConnectionItem(scenario_node, notes_node)
            self.scene.addItem(connection)
            self.connections.append(connection)

    def auto_layout(self):
        """Auto layout"""
        if not self.nodes:
            return

        # Simple force-directed layout
        for iteration in range(10):
            # Calculate repulsion
            for node1_id, node1 in self.nodes.items():
                fx, fy = 0, 0
                for node2_id, node2 in self.nodes.items():
                    if node1_id != node2_id:
                        dx = node1.x() - node2.x()
                        dy = node1.y() - node2.y()
                        dist = max(dx * dx + dy * dy, 100)
                        force = 5000 / dist
                        fx += dx * force / dist
                        fy += dy * force / dist

                # Apply force
                new_x = node1.x() + fx
                new_y = node1.y() + fy
                node1.setPos(new_x, new_y)

        # Fit view to content
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def zoom_in(self):
        """Zoom in"""
        if self._scale_factor < self._max_scale:
            self.scale(1.2, 1.2)
            self._scale_factor *= 1.2

    def zoom_out(self):
        """Zoom out"""
        if self._scale_factor > self._min_scale:
            self.scale(0.8, 0.8)
            self._scale_factor *= 0.8

    def reset_zoom(self):
        """Reset zoom"""
        self.resetTransform()
        self._scale_factor = 1.0


class BDDMindMapDock(QWidget):
    """BDD mind map dock widget"""

    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.bdd_converter = BDDConverter()
        self.current_scenarios = []
        
        # Initialize keyword highlighter
        self.keyword_highlighter = KeywordHighlighter()

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setToolTip("Reload BDD test cases")
        toolbar_layout.addWidget(self.refresh_btn)

        toolbar_layout.addStretch()

        # Zoom controls
        toolbar_layout.addWidget(QLabel("Zoom:"))

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setToolTip("Zoom in")
        self.zoom_in_btn.setMaximumWidth(30)
        toolbar_layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setToolTip("Zoom out")
        self.zoom_out_btn.setMaximumWidth(30)
        toolbar_layout.addWidget(self.zoom_out_btn)

        # Auto layout button
        self.auto_layout_btn = QPushButton("Auto Layout")
        self.auto_layout_btn.setToolTip("Automatically adjust node layout")
        toolbar_layout.addWidget(self.auto_layout_btn)

        layout.addWidget(toolbar)

        # Mind map view
        self.mind_map_view = BDDMindMapView()
        layout.addWidget(self.mind_map_view)

        # Status bar
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 2, 5, 2)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.node_count_label = QLabel("Nodes: 0")
        self.node_count_label.setStyleSheet("color: gray; font-size: 10px;")
        status_layout.addWidget(self.node_count_label)

        layout.addWidget(status_frame)

    def _setup_connections(self):
        """Setup signal connections"""
        self.refresh_btn.clicked.connect(self.refresh_bdd_data)
        self.zoom_in_btn.clicked.connect(self.mind_map_view.zoom_in)
        self.zoom_out_btn.clicked.connect(self.mind_map_view.zoom_out)
        self.auto_layout_btn.clicked.connect(self.auto_layout)

        self.mind_map_view.node_clicked.connect(self.on_node_clicked)

    def refresh_bdd_data(self):
        """Refresh BDD data"""
        try:
            self.status_label.setText("Loading BDD test cases...")

            # Here the test case files should be loaded from the project
            # Using sample data for now
            self.load_sample_data()

            self.update_mind_map()
            self.status_label.setText(f"Loaded {len(self.current_scenarios)} scenarios")

        except Exception as e:
            self.status_label.setText(f"Load failed: {str(e)}")

    def load_sample_data(self):
        """Load sample data"""
        self.current_scenarios = [
            {
                'title': 'User login functionality test',
                'given': [
                    {'content': 'User has registered an account', 'number': '1. '},
                    {'content': 'System is running normally', 'number': '2. '}
                ],
                'when': [
                    {'content': 'User enters correct username and password', 'number': '1. '},
                    {'content': 'User clicks the login button', 'number': '2. '}
                ],
                'then': [
                    {'content': 'System verifies user information', 'number': '1. '},
                    {'content': 'User logs in successfully and is redirected to the homepage', 'number': '2. '}
                ],
                'notes': 'Need to test various edge cases'
            },
            {
                'title': 'Product search functionality test',
                'given': [
                    {'content': 'There is product data in the database', 'number': '1. '}
                ],
                'when': [
                    {'content': 'User enters keywords in the search box', 'number': '1. '},
                    {'content': 'User clicks the search button', 'number': '2. '}
                ],
                'then': [
                    {'content': 'System returns a list of related products', 'number': '1. '},
                    {'content': 'Search results are sorted by relevance', 'number': '2. '}
                ],
                'notes': 'Test search performance and accuracy'
            }
        ]

    def update_mind_map(self):
        """Update mind map"""
        print(f"[BDD-MINDMAP] update_mind_map called with {len(self.current_scenarios)} scenarios")
        self.mind_map_view.clear_graph()

        for i, scenario in enumerate(self.current_scenarios):
            print(f"[BDD-MINDMAP] Adding scenario {i}: {scenario.get('title', 'No title')}")
            self.mind_map_view.add_bdd_scenario(scenario, i)

        # Update node count
        node_count = len(self.mind_map_view.nodes)
        print(f"[BDD-MINDMAP] Total nodes created: {node_count}")
        self.node_count_label.setText(f"Nodes: {node_count}")

        # Auto layout
        print(f"[BDD-MINDMAP] Scheduling auto layout")
        QTimer.singleShot(100, self.auto_layout)

    def auto_layout(self):
        """Perform auto layout"""
        self.mind_map_view.auto_layout()

    def on_node_clicked(self, node_type: str, node_data: dict):
        """Handle node click event"""
        self.status_label.setText(f"Clicked {node_type} node")

    def load_bdd_from_files(self, file_paths: List[str]):
        """Load BDD data from files"""
        try:
            all_scenarios = []

            for file_path in file_paths:
                if file_path.endswith('.md'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Convert to BDD format
                    bdd_content = self.bdd_converter.convert_to_bdd(content)

                    # Parse BDD scenarios
                    scenarios = self.bdd_converter._parse_bdd_scenarios(bdd_content)
                    all_scenarios.extend(scenarios)

            self.current_scenarios = all_scenarios
            self.update_mind_map()
            self.status_label.setText(f"Loaded {len(all_scenarios)} scenarios")

        except Exception as e:
            self.status_label.setText(f"Load failed: {str(e)}")
    
    def load_bdd_from_file(self, file_path: str):
        """Load BDD data from a single file"""
        try:
            if not file_path or not file_path.endswith('.md'):
                self.current_scenarios = []
                self.update_mind_map()
                self.status_label.setText("No valid file selected")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Convert to BDD format
            bdd_content = self.bdd_converter.convert_to_bdd(content)

            # Parse BDD scenarios
            scenarios = self.bdd_converter._parse_bdd_scenarios(bdd_content)
            
            self.current_scenarios = scenarios
            self.update_mind_map()
            
            # Update status
            import os
            file_name = os.path.basename(file_path)
            self.status_label.setText(f"Loaded {len(scenarios)} scenarios from {file_name}")

        except Exception as e:
            self.current_scenarios = []
            self.update_mind_map()
            self.status_label.setText(f"Load failed: {str(e)}")
    
    def load_bdd_from_content(self, file_path: str, content: str):
        """Load BDD data from file content directly"""
        try:
            print(f"[BDD-MINDMAP] load_bdd_from_content called with file_path: {file_path}")
            print(f"[BDD-MINDMAP] Content length: {len(content) if content else 0}")
            
            if not file_path or not file_path.endswith('.md'):
                self.current_scenarios = []
                self.update_mind_map()
                self.status_label.setText("No valid file selected")
                return
            
            if not content or not content.strip():
                self.current_scenarios = []
                self.update_mind_map()
                self.status_label.setText("Empty file")
                return

            # Convert to BDD format
            bdd_content = self.bdd_converter.convert_to_bdd(content)
            print(f"[BDD-MINDMAP] BDD content: {bdd_content[:200]}...")

            # Parse BDD scenarios
            scenarios = self.bdd_converter._parse_bdd_scenarios(bdd_content)
            print(f"[BDD-MINDMAP] Parsed {len(scenarios)} scenarios")
            
            self.current_scenarios = scenarios
            self.update_mind_map()
            
            # Update status
            import os
            file_name = os.path.basename(file_path)
            self.status_label.setText(f"Loaded {len(scenarios)} scenarios from {file_name}")

        except Exception as e:
            # Don't clear scenarios on error to avoid flickering
            print(f"[BDD-MINDMAP] Error in load_bdd_from_content: {str(e)}")
            self.status_label.setText(f"Parse error: {str(e)}")
    
    # Keyword highlighting methods - delegate to mind_map_view
    def set_highlight_keywords(self, keywords: list):
        """设置要高亮的关键字列表"""
        print(f"BDDMindMapDock.set_highlight_keywords called with: {keywords}")
        if hasattr(self.mind_map_view, 'set_highlight_keywords'):
            print(f"Calling mind_map_view.set_highlight_keywords with {keywords}")
            self.mind_map_view.set_highlight_keywords(keywords)
        else:
            print("mind_map_view does not have set_highlight_keywords method")
    
    def add_highlight_keyword(self, keyword: str):
        """添加单个关键字进行高亮"""
        if hasattr(self.mind_map_view, 'add_highlight_keyword'):
            self.mind_map_view.add_highlight_keyword(keyword)
    
    def remove_highlight_keyword(self, keyword: str):
        """移除关键字高亮"""
        if hasattr(self.mind_map_view, 'remove_highlight_keyword'):
            self.mind_map_view.remove_highlight_keyword(keyword)
    
    def clear_highlight_keywords(self):
        """清除所有关键字高亮"""
        if hasattr(self.mind_map_view, 'clear_highlight_keywords'):
            self.mind_map_view.clear_highlight_keywords()
    
    def set_highlight_color(self, color):
        """设置高亮颜色"""
        if hasattr(self.mind_map_view, 'set_highlight_color'):
            self.mind_map_view.set_highlight_color(color)
    
    def get_highlight_keywords(self) -> list:
        """获取当前的关键字列表"""
        if hasattr(self.mind_map_view, 'get_highlight_keywords'):
            return self.mind_map_view.get_highlight_keywords()
        return []


