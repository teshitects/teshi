from queue import Empty

from IPython.external.qt_for_kernel import QtCore
from PySide6.QtCore import QObject, Signal
from jupyter_client import KernelManager
from teshi.utils import graph_util
from teshi.utils.str_util import format_jupyter_traceback


class GraphExecuteController(QObject):
    executor_started = Signal()
    executor_process = Signal(str)
    executor_binding = Signal(str)
    executor_stopped = Signal()

    def __init__(self, graph: dict, nodes: dict,notebook_dir, tab_id, single_node_id=None,parent=None):
        super().__init__(parent)
        self.graph = graph
        self.nodes = nodes
        self.notebook_dir = notebook_dir
        self.kernel_manager = None
        self.kernel_client = None
        self.tab_id = tab_id
        self.single_node_id = single_node_id

    def start(self):
        self.kernel_manager = KernelManager(kernel_name="python3")
        self.kernel_manager.start_kernel()
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.load_connection_file()
        self.kernel_client.execute(f"%cd {self.notebook_dir}")
        self.kernel_client.start_channels()
        self.kernel_client.wait_for_ready()

    def execute_all(self):
        self.start()
        # 1. Execute all nodes in topological order
        topo_order = graph_util.topological_sort(self.graph)
        print(topo_order)
        # 2. Execute
        for node_id in topo_order:
            self.execute(self.nodes[node_id][0], self.nodes[node_id][1], self.tab_id)
        # self.shutdown()
        # self.executor_stopped.emit()


    def execute_single_node_and_its_parents(self):
        if self.single_node_id is None:
            return
        self.start()
        topo_order_node_parent = graph_util.topological_sort_node_parent(self.graph, self.single_node_id)
        for order_id in topo_order_node_parent:
            if order_id is not None:
                self.execute(self.nodes[order_id][0], self.nodes[order_id][1], self.tab_id)

    def execute(self, code, uuid, tab_id):
        msg_id = self.kernel_client.execute(code)
        self.executor_binding.emit(f"{msg_id}:{tab_id}#{uuid}")
        while True:
            try:
                msg = self.kernel_client.get_iopub_msg(timeout=0.1)
                # self.executor_process.emit(f" {code.split('\n')[0]}: {msg}")
                print(f"{code.split('\n')[0]}: {msg}")
                content = msg["content"]
                parent_msg_id = msg["parent_header"]["msg_id"]
                if msg["msg_type"] == "stream" and content["name"] == "stdout":
                    self.executor_process.emit(f"{parent_msg_id}#{tab_id}:stream:{content['text']}")
                    # break
                elif msg["msg_type"] == "error":
                    self.executor_process.emit(f"{parent_msg_id}#{tab_id}:error_:{content['ename']}: {content['evalue']}\n{format_jupyter_traceback(content['traceback'])}")
                    # break
                elif msg["msg_type"] == "execute_input":
                    self.executor_process.emit(f"{parent_msg_id}#{tab_id}:execute_input: content['code']")
                elif msg["msg_type"] == "status":
                    self.executor_process.emit(f"{parent_msg_id}#{tab_id}:status:{content['execution_state']}")
                    if content["execution_state"] == "idle" and msg_id == msg["parent_header"]["msg_id"]:
                        break

            except KeyboardInterrupt:
                print("Interrupted by user.")
                break
            except Empty:
                # If no messages are available, we'll end up here, but we can just continue and try again.
                pass

    def shutdown(self):
        '''
            Don't know why, but I should use it: Shut down the kernel and the client.
            https://github.com/jupyter/jupyter_client/issues/1026#issuecomment-2726203528
        '''
        if self.kernel_client:
            self.kernel_client.stop_channels()
            self.kernel_client = None
        if self.kernel_manager:
            self.kernel_manager.shutdown_kernel()
            self.kernel_manager = None


