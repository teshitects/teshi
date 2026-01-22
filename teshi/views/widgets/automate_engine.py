import datetime
import sys
import uuid
from pathlib import Path

from teshi.utils.logger import get_logger

from PySide6 import QtGui, QtWidgets, QtCore
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QDockWidget, QMainWindow, QListWidget, QTabWidget, QTextEdit, QFrame, QWidget, \
    QVBoxLayout, QApplication, QPushButton

from src.controllers.graph_execute_controller import GraphExecuteController
from src.models.JupyterNodeModel import JupyterNodeModel
from src.utils.yaml_graph_util import load_graph_from_yaml, save_graph_to_yaml
from src.managers.node_lib_manager import NodeLibManager
from src.views.widgets.yaml_tab import YamlTab
from src.views.JupyterVisualRunnerEditor import *


class JupyterVisualRunner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Jupyter Visual Runner", "Jupyter Visual Runner")
        self.recent_files = self.settings.value("RecentFiles", [])
        if self.recent_files is None:
            self.recent_files = []
        self.node_lib_manager = NodeLibManager()
        self.logger = get_logger()
        self.setup_node_sketchpad()
        self.center()
        self.thread1 = None

    def closeEvent(self, event):
        # Save QDockWidget state
        self.settings.setValue('windowState', self.saveState())

    def add_tab_without_filepath(self):
        # 1. Open file chooser to get the .yaml file path
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "", "Workflow (*.yaml)")
        if file_path == '':
            return
        self.recent_files.append(file_path)
        self.settings.setValue("RecentFiles", self.recent_files)
        self.add_tab(file_path)

    # MVP: 200 line to restructure the code
    # MVP: 200 line to restructure the code
    def add_tab(self, file_path):
        """ Add a new tab"""
        # 2. Load the .yaml file
        graph_data = load_graph_from_yaml(file_path)
        nodes_data = graph_data.get('nodes', [])
        connections_data = graph_data.get('connections', [])

        # 3. Init tab
        tab_id = str(uuid.uuid1())
        notebook_dir = Path(file_path).parent.resolve()
        scene = NodeSketchpadScene()
        view = NodeSketchpadView(scene, self)
        view.setAlignment(Qt.AlignCenter)
        title = file_path.split('/')[-1]
        
        tab_container = YamlTab(title, tab_id, notebook_dir, file_path, graph_data, scene, view)
        layout = QVBoxLayout(tab_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)
        self.center_tabs.addTab(tab_container, title)

        # 4. Create Nodes
        graph_nodes = {}
        for node_data in nodes_data:
            node_title = node_data['title']
            # Get code from library, fallback to empty string
            node_code = self.node_lib_manager.get_node_code(node_title)
            
            node_model = JupyterNodeModel(node_title, node_code)
            node_model.tab_id = tab_id
            node_model.uuid = node_data.get('id', str(uuid.uuid4()))
            node_model.params = node_data.get('params', {})
            node_model.x = node_data.get('pos', [0, 0])[0]
            node_model.y = node_data.get('pos', [0, 0])[1]
            
            # Create graphic item
            graph_node = JupyterGraphNode(node_model.title, node_model.code)
            # Sync model data
            graph_node.data_model = node_model
            graph_node.setPos(node_model.x, node_model.y)
            graph_node.signals.nodeClicked.connect(self.update_widget)
            
            scene.addItem(graph_node)
            graph_nodes[node_title] = graph_node

        # 5. Draw the connections
        for conn_data in connections_data:
            from_node = graph_nodes.get(conn_data['from'])
            to_node = graph_nodes.get(conn_data['to'])
            
            if from_node and to_node:
                connection = ConnectionItem(from_node, to_node)
                scene.addItem(connection)
                from_node.add_connection(connection)
                to_node.add_connection(connection)
                # Update model children relationships
                if to_node.data_model.title not in from_node.data_model.children:
                    from_node.data_model.children.append(to_node.data_model.title)

        self.center_tabs.setCurrentWidget(tab_container)

    def save_tab(self):
        current_widget = self.center_tabs.currentWidget()
        if current_widget is None:
            return
        if isinstance(current_widget, YamlTab):
            # 1. Collect Nodes and Connections from Scene
            nodes_data = []
            connections_data = []
            
            graph_nodes = {}
            for item in current_widget.scene.items():
                if isinstance(item, JupyterGraphNode):
                    graph_nodes[item.data_model.title] = item
                    
                    # Update global library with current code
                    self.node_lib_manager.save_node_code(item.data_model.title, item.data_model.code)
                    
                    node_data = {
                        "id": item.data_model.uuid,
                        "title": item.data_model.title,
                        "pos": [item.pos().x(), item.pos().y()],
                        "params": item.data_model.params
                    }
                    nodes_data.append(node_data)
            
            # Connections
            # We iterate nodes and check their connections to avoid duplicates if possible
            # Or just iterate all connection items if we can distinguish them
            visited_conns = set()
            for item in current_widget.scene.items():
                if isinstance(item, ConnectionItem): # Assuming ConnectionItem is available or imported
                    # Verify if this connection is already added
                    if item in visited_conns:
                        continue
                    visited_conns.add(item)
                    
                    conn_data = {
                        "from": item.source.data_model.title,
                        "to": item.destination.data_model.title
                    }
                    connections_data.append(conn_data)

            graph_data = {
                "nodes": nodes_data,
                "connections": connections_data
            }
            
            # 2. Save to file
            save_graph_to_yaml(graph_data, current_widget.file_path)
            self.node_lib_manager.save_library()

    def restore(self):
        current_widget = self.center_tabs.currentWidget()
        if current_widget is None:
            return
        for item in current_widget.scene.items():
            if isinstance(item, JupyterGraphNode):
                item.set_default_color()
                item.set_default_text()
                item.data_model.last_status = ""

    def run_tab(self):
        current_tab_widget = self.center_tabs.currentWidget()
        if current_tab_widget is None:
            return
        if isinstance(current_tab_widget, YamlTab):
            graph = {item.data_model.title:item.data_model.children for item in current_tab_widget.scene.items() if isinstance(item, JupyterGraphNode)}
            # Update nodes structure to [code, uuid, params]
            nodes = {item.data_model.title:[item.data_model.code, item.data_model.uuid, item.data_model.params] for item in current_tab_widget.scene.items() if isinstance(item, JupyterGraphNode)}

            self.restore()
            if self.thread1 is not None:
                self.thread1.quit()
                self.thread1.wait()

            self.thread1 = QtCore.QThread()
            self.worker = GraphExecuteController(graph, nodes, current_tab_widget.notebook_dir, current_tab_widget.tab_id)
            self.worker.moveToThread(self.thread1)
            self.worker.executor_process.connect(self.update_process)
            self.worker.executor_binding.connect(self.bind_item_msg_id)
            self.thread1.started.connect(self.worker.execute_all)
            self.thread1.start()

    def run_single_node_and_parent(self):
        """ Run the selected node and its parents"""
        current_tab_widget = self.center_tabs.currentWidget()
        if current_tab_widget is None:
            return
        if isinstance(current_tab_widget, YamlTab):
            graph = {item.data_model.title: item.data_model.children for item in current_tab_widget.scene.items() if isinstance(item, JupyterGraphNode)}
            # Update nodes structure to [code, uuid, params]
            nodes = {item.data_model.title:[item.data_model.code, item.data_model.uuid, item.data_model.params] for item in current_tab_widget.scene.items() if isinstance(item, JupyterGraphNode)}

            # Clear the scene
            self.restore()
            if self.thread1 is not None:
                self.thread1.quit()
                self.thread1.wait()

            self.thread1 = QtCore.QThread()
            self.worker = GraphExecuteController(graph, nodes, current_tab_widget.notebook_dir, current_tab_widget.tab_id, current_tab_widget.scene.selectedItems()[0].data_model.title)
            self.worker.moveToThread(self.thread1)
            self.worker.executor_process.connect(self.update_process)
            self.worker.executor_binding.connect(self.bind_item_msg_id)
            # When using connect, you don't need to add '()' after the function.
            self.thread1.started.connect(self.worker.execute_single_node_and_its_parents)
            self.thread1.start()

    def bind_item_msg_id(self, binding):
        msg_id = binding.split(":")[0]
        tab_id = binding.split(":")[1].split("#")[0]
        item_id = binding.split(":")[1].split("#")[1]
        self.logger.info(f"Binding: {binding}")
        for index in range(self.center_tabs.count()):
            tab_widget = self.center_tabs.widget(index)
            if getattr(tab_widget, 'tab_id', None) == tab_id:
                    for item in tab_widget.scene.items():
                        if isinstance(item, JupyterGraphNode):
                            if item.data_model.uuid == item_id:
                                item.data_model.msg_id = msg_id

    def update_process(self, process):
        process_msg_id = process.split(":")[0].split("#")[0]
        tab_id = process.split(":")[0].split("#")[1]
        print(process)
        for index in range(self.center_tabs.count()):
            tab_widget = self.center_tabs.widget(index)
            if getattr(tab_widget, 'tab_id', None) == tab_id:
                    for item in tab_widget.scene.items():
                        if isinstance(item, JupyterGraphNode):
                            if item.data_model.msg_id == process_msg_id:
                                status_str = process.replace(f"{process_msg_id}#{tab_id}:", "")
                                print(status_str)
                                if status_str == "status:busy":
                                    color = QColor('yellow')
                                    item.set_color(color)
                                    item.data_model.last_status = "status:busy"
                                if status_str.startswith("execute_input"):
                                    color = QColor('yellow')
                                    item.set_color(color)
                                    item.data_model.last_status = "execute_input"
                                elif status_str == "status:idle" and item.data_model.last_status == "status:busy":
                                    return
                                elif status_str == "status:idle" and item.data_model.last_status != "error":
                                    color = QColor('green')
                                    item.set_color(color)
                                    item.data_model.last_status = "idle"
                                elif status_str.startswith("error"):
                                    color = QColor('red')
                                    item.set_color(color)
                                    item.data_model.last_status = "error"
                                    item.set_result_text(status_str.replace("error_:","").split("\n")[0])
                                    item.data_model.result = status_str.replace("error_:", "")
                                elif status_str.startswith("stream"):
                                    item.data_model.last_status = "stream"
                                    item.set_result_text(status_str.replace('stream:', "").split("\n")[0])
                                    item.data_model.result = status_str.replace("stream:", "")




                                print(f"{datetime.datetime.now()} {item.data_model.title}: {status_str}")
                    self.logger.info(process)


    def setup_node_sketchpad(self):
        self.setWindowTitle("Jupyter Visual Runner")
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowIcon(QtGui.QIcon("public/icon.png"))

        self.center_tabs = QTabWidget()
        homepage = QWidget()
        layout = QVBoxLayout(homepage)
        layout = QVBoxLayout(homepage)
        layout.setContentsMargins(0, 0, 0, 0)
        self.center_tabs.addTab(homepage, "Homepage")
        self.setCentralWidget(self.center_tabs)
        # Show all recent files and filepath in the homepage, and clickable
        if self.recent_files is not None:
            for file_path in self.recent_files:
                recent_file_button = QPushButton(file_path)
                layout.addWidget(recent_file_button)
                recent_file_button.clicked.connect(lambda _, path=file_path: self.add_tab(path))




        dock1 = QDockWidget("Browser", self)
        dock1_widget = QListWidget()
        dock1.setWidget(dock1_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock1)



        # node raw code Dock
        raw_code_dock = QDockWidget("Raw", self)
        self.raw_code_widget = QTextEdit()
        self.raw_code_widget.setLineWrapMode(QTextEdit.NoWrap)
        raw_code_dock.setWidget(self.raw_code_widget)
        self.raw_code_widget.setFont(NodeEditorConfig.node_title_font)
        self.addDockWidget(Qt.RightDockWidgetArea, raw_code_dock)

        properties_dock = QDockWidget("Properties", self)
        properties_dock_widget = QListWidget()
        properties_dock.setWidget(properties_dock_widget)
        self.tabifyDockWidget(raw_code_dock, properties_dock)

        # result Dock
        result_dock = QDockWidget("Result", self)
        self.result_widget = QTextEdit()
        self.result_widget.setReadOnly(True)
        self.result_widget.setFont(NodeEditorConfig.node_title_font)
        self.result_widget.setLineWrapMode(QTextEdit.NoWrap)
        result_dock.setWidget(self.result_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, result_dock)


        
        button_group = QDockWidget("Button Group", self)
        button_group_widget = QWidget()
        button_group.setWidget(button_group_widget)
        button_group_layout = QVBoxLayout(button_group_widget)
        button_group_layout.setContentsMargins(0, 0, 0, 0)
        add_tab_button = QtWidgets.QPushButton("Add Tab")
        save_tab_button = QtWidgets.QPushButton("Save Tab")

        run_button = QtWidgets.QPushButton("Run ALL")
        run_single_node_button = QtWidgets.QPushButton("Run Single")
        run_single_node_button.clicked.connect(self.run_single_node_and_parent)
        save_code_button = QtWidgets.QPushButton("Save Code")
        save_code_button.clicked.connect(self.update_graph_node_code)

        restore_button = QtWidgets.QPushButton("Restore Status")
        restore_button.clicked.connect(self.restore)

        button_group_layout.addWidget(save_code_button)
        button_group_layout.addWidget(run_single_node_button)
        button_group_layout.addWidget(run_button)
        button_group_layout.addWidget(restore_button)
        button_group_layout.addWidget(add_tab_button)
        button_group_layout.addWidget(save_tab_button)
        add_tab_button.clicked.connect(self.add_tab_without_filepath)
        save_tab_button.clicked.connect(self.save_tab)
        run_button.clicked.connect(self.run_tab)

        self.addDockWidget(Qt.BottomDockWidgetArea, button_group)




        # Temporarily hide this widget
        # dock4 = QDockWidget("Result", self)
        web_view = QWebEngineView()
        web_view.setHtml(
            '<a href="https://data.typeracer.com/pit/profile?user=hk_l&ref=badge" target="_top"><img src="https://data.typeracer.com/misc/badge?user=hk_l" border="0" alt="TypeRacer.com scorecard for user hk_l"/></a>')
        # dock4.setWidget(web_view)
        # dock4.setEnabled(False)
        # self.addDockWidget(Qt.RightDockWidgetArea, dock4)

    def center(self):
        # Get the center point of the screen
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        center_point = screen_geometry.center()
        # Align the geometric center of the window to the center of the screen
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(center_point)

        self.move(window_geometry.topLeft())

    def update_widget(self, data_model_dict):
        self.raw_code_widget.setText(data_model_dict["code"])
        self.result_widget.setText(data_model_dict["result"])
        # set uuid in tooltip
        self.result_widget.setToolTip(data_model_dict['uuid'])



    def update_graph_node_code(self):
        # get the current tab
        current_tab = self.center_tabs.currentWidget()
        if current_tab is None:
            return
        if isinstance(current_tab, YamlTab):
            # get the current scene
            scene = current_tab.scene
            # get specific node by uuid
            for item in scene.items():
                if isinstance(item, JupyterGraphNode):
                    if item.data_model.uuid == self.result_widget.toolTip():
                        item.data_model.code = self.raw_code_widget.toPlainText()
                        item.data_model.code_changed = True
                        if item.data_model.code.split('\n')[0] != item.data_model.title:
                            self.item_title_changed(item)
                        else:
                            # Save code to library immediately or wait for save?
                            self.node_lib_manager.save_node_code(item.data_model.title, item.data_model.code)
                        
                        # Refresh IO widgets
                        item.update_input_widgets()
                        item.update() # Force repaint

    def item_title_changed(self, item):
        old_title =  item.data_model.title
        new_title = item.data_model.code.split('\n')[0]

        # current tab
        current_tab = self.center_tabs.currentWidget()
        if current_tab is None:
            return
        if isinstance(current_tab, YamlTab):
            # get the current scene
            scene = current_tab.scene
            # Update NodeLib: save new code under new title
            self.node_lib_manager.save_node_code(new_title, item.data_model.code)
            # We don't delete old title from library as other nodes might use it
            # check all node connections
            for item1 in scene.items():
                if isinstance(item1, JupyterGraphNode):
                    if old_title in item1.data_model.children:
                        item1.data_model.children.remove(old_title)
                        item1.data_model.children.append(new_title)
                    for connection in item1.connections:
                        if connection.source.data_model.title == old_title:
                            connection.source.data_model.title = new_title
                        if connection.destination.data_model.title == old_title:
                            connection.destination.data_model.title = new_title
        item.data_model.title = new_title
        item._title = new_title
        item.set_title_text(new_title)




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    jupyter_visual_runner = JupyterVisualRunner()

    # Load QDockWidget state
    # the companyName and appName is necessary to save DockWidget state, I don't know why.
    settings = QSettings("Jupyter Visual Runner", "Jupyter Visual Runner")
    state = settings.value('windowState')
    if state != None:
        jupyter_visual_runner.restoreState(state)

    jupyter_visual_runner.show()
    app.exec()