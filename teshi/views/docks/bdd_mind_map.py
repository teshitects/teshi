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
        """Set node color"""
        colors = {
            'scenario': QColor(52, 152, 219),  # Blue
            'given': QColor(46, 204, 113),  # Green
            'when': QColor(241, 196, 15),  # Yellow
            'then': QColor(231, 76, 60),  # Red
            'notes': QColor(155, 89, 182)  # Purple
        }

        color = colors.get(self.node_type, QColor(149, 165, 166))
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.white, 2))

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

        self.setPen(QPen(QColor(100, 100, 100, 150), 2, Qt.SolidLine))

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
        self.setScene(self.scene)

        # Setup view properties
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Node storage
        self.nodes = {}
        self.connections = []

        # Layout parameters
        self.level_height = 100
        self.node_spacing = 120

        # Zoom control
        self._scale_factor = 1.0
        self._min_scale = 0.3
        self._max_scale = 3.0

    def wheelEvent(self, event: QWheelEvent):
        """Mouse wheel zoom"""
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        # Save original scene position
        old_pos = self.mapToScene(event.pos())

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        if self._min_scale < self._scale_factor * zoom_factor < self._max_scale:
            self.scale(zoom_factor, zoom_factor)
            self._scale_factor *= zoom_factor

        # Get new position
        new_pos = self.mapToScene(event.pos())

        # Adjust scene position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def clear_graph(self):
        """Clear graphics"""
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()

    def add_bdd_scenario(self, scenario_data: dict, scenario_index: int):
        """Add BDD scenario to the graph"""
        # Scenario node
        scenario_x = scenario_index * 300
        scenario_y = 50

        scenario_node = BDDNodeItem(
            'scenario',
            scenario_data['title'],
            scenario_data.get('notes', ''),
            scenario_x,
            scenario_y
        )
        self.scene.addItem(scenario_node)
        self.nodes[f'scenario_{scenario_index}'] = scenario_node

        # Current Y position
        current_y = scenario_y + self.level_height

        # Given nodes
        if scenario_data.get('given'):
            given_x = scenario_x - 150
            for i, given in enumerate(scenario_data['given']):
                given_content = given['content'] if isinstance(given, dict) else given
                given_node = BDDNodeItem('given', given_content, '', given_x, current_y)
                self.scene.addItem(given_node)
                self.nodes[f'given_{scenario_index}_{i}'] = given_node

                # Connect to scenario
                connection = BDDConnectionItem(scenario_node, given_node)
                self.scene.addItem(connection)
                self.connections.append(connection)

                current_y += self.level_height

        # When nodes
        if scenario_data.get('when'):
            when_x = scenario_x
            for i, when in enumerate(scenario_data['when']):
                when_content = when['content'] if isinstance(when, dict) else when
                when_node = BDDNodeItem('when', when_content, '', when_x, current_y)
                self.scene.addItem(when_node)
                self.nodes[f'when_{scenario_index}_{i}'] = when_node

                # Connect to scenario
                connection = BDDConnectionItem(scenario_node, when_node)
                self.scene.addItem(connection)
                self.connections.append(connection)

                current_y += self.level_height

        # Then nodes
        if scenario_data.get('then'):
            then_x = scenario_x + 150
            for i, then in enumerate(scenario_data['then']):
                then_content = then['content'] if isinstance(then, dict) else then
                then_node = BDDNodeItem('then', then_content, '', then_x, current_y)
                self.scene.addItem(then_node)
                self.nodes[f'then_{scenario_index}_{i}'] = then_node

                # Connect to scenario
                connection = BDDConnectionItem(scenario_node, then_node)
                self.scene.addItem(connection)
                self.connections.append(connection)

                current_y += self.level_height

        # Notes node
        if scenario_data.get('notes'):
            notes_x = scenario_x + 300
            notes_node = BDDNodeItem('notes', 'Notes', scenario_data['notes'], notes_x, scenario_y)
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
        self.mind_map_view.clear_graph()

        for i, scenario in enumerate(self.current_scenarios):
            self.mind_map_view.add_bdd_scenario(scenario, i)

        # Update node count
        node_count = len(self.mind_map_view.nodes)
        self.node_count_label.setText(f"Nodes: {node_count}")

        # Auto layout
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

            # Parse BDD scenarios
            scenarios = self.bdd_converter._parse_bdd_scenarios(bdd_content)
            
            self.current_scenarios = scenarios
            self.update_mind_map()
            
            # Update status
            import os
            file_name = os.path.basename(file_path)
            self.status_label.setText(f"Loaded {len(scenarios)} scenarios from {file_name}")

        except Exception as e:
            # Don't clear scenarios on error to avoid flickering
            self.status_label.setText(f"Parse error: {str(e)}")


