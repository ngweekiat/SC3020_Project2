"""
interface.py
-------------
Purpose:
    - Manages the graphical user interface (GUI) for the application.
    - Allows users to generate QEPs, modify them (What-If analysis), and retrieve AQPs.

Requirements:
    1. Allow users to:
        - Input SQL queries via a Query panel.
        - View the QEP (Query Execution Plan) in a visual tree format.
        - Interactively edit the QEP to pose what-if questions (e.g., changing operators or join orders).
        - View the modified SQL query and the corresponding AQP.
        - Compare the costs of the AQP with the original QEP.
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QScrollArea, QGridLayout, QTreeWidgetItemIterator, QLineEdit, QVBoxLayout, QPushButton, QTextEdit, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from whatif import WhatIfAnalysis
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtGui import QColor, QFont
from graphviz import Digraph
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene



from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout
from PyQt6.QtCore import Qt
import dotenv
import os

dotenv.load_dotenv()

# Prepopulate login details
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "tpch")

class Login(QDialog):
    """
    Login dialog to authenticate users before accessing the main interface.
    """
    def __init__(self):
        super().__init__()

        # Set up login window title and size
        self.setWindowTitle("Login")
        self.setFixedSize(400, 300)

        # Labels and input fields for host, port, user, and password
        self.host_label = QLabel("Host:")
        self.host_input = QLineEdit(self)
        self.host_input.setText(DB_HOST)  # Prepopulate host

        self.port_label = QLabel("Port No:")
        self.port_input = QLineEdit(self)
        self.port_input.setText(DB_PORT)  # Prepopulate port

        self.user_label = QLabel("Username:")
        self.user_input = QLineEdit(self)
        self.user_input.setText(DB_USER)  # Prepopulate username

        self.pass_label = QLabel("Password:")
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setText(DB_PASSWORD)  # Prepopulate password

        # Login button
        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.login)


        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.host_label)
        layout.addWidget(self.host_input)
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_input)
        layout.addWidget(self.user_label)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def login(self):
        # Capture login details
        host = self.host_input.text()
        port = self.port_input.text()
        user = self.user_input.text()
        password = self.password_input.text()

        # Perform login validation (you can customize this to connect to a DB or API)
        if host and port and user and password:
            self.accept()  # Close login dialog and proceed with the application
        else:
            self.show_error("All fields are required.")
    
    def show_error(self, message):
        error_dialog = Error(message)
        error_dialog.exec()


class Error(QDialog):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
        self.setWindowTitle("Error")
        self.setFixedSize(300, 150)

        # Error label
        self.error_label = QLabel(self.msg, self)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Acknowledge button
        self.ack_button = QPushButton("Acknowledge", self)
        self.ack_button.clicked.connect(self.close)

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.error_label)
        layout.addWidget(self.ack_button)

        self.setLayout(layout)


class QEPInterface(QWidget):
    """
    GUI to visualize and modify Query Execution Plans (QEP).
    """
    def __init__(self):
        super().__init__()

        # Display login first
        self.login_dialog = Login()
        if self.login_dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit()  # Exit if login is unsuccessful
            
        # Proceed with the rest of the interface setup
        self.setWindowTitle("QEP and AQP What-If Analysis")
        
        # Set a standard window size after login
        self.resize(1200, 800)  # Resize the window to 1200x800
        # Initialize What-If Analysis Class
        self.whatif = WhatIfAnalysis()

        # Main layout
        main_layout = QVBoxLayout(self)

        # Create a scrollable area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.container_widget = QWidget()
        self.grid_layout = QGridLayout(self.container_widget)
        self.scroll_area.setWidget(self.container_widget)
        main_layout.addWidget(self.scroll_area)

        # Section 1: SQL Input Area
        self.query_input_label = QLabel("Enter SQL Query:")
        self.query_input_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.query_input = QTextEdit(self)
        self.query_input.setPlaceholderText("Enter SQL query here")
        self.query_input.setFixedHeight(60)

        self.grid_layout.addWidget(self.query_input_label, 0, 0, 1, 3)
        self.grid_layout.addWidget(self.query_input, 1, 0, 1, 3)

        # Section 2: Execution Options
        self.run_query_button = QPushButton("Generate QEP")
        self.run_query_button.clicked.connect(self.generate_qep)

        self.modify_qep_button = QPushButton("Modify QEP (What-If Analysis)")
        self.modify_qep_button.clicked.connect(self.modify_qep)
        self.modify_qep_button.setEnabled(False)


        self.grid_layout.addWidget(self.run_query_button, 3, 0, 1, 1)
        self.grid_layout.addWidget(self.modify_qep_button, 3, 1, 1, 1)

        # Section 3: Outputs
        self.sql_output_label = QLabel("Modified SQL Query:")
        self.sql_output_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.sql_output = QTextEdit(self)
        self.sql_output.setReadOnly(True)
        self.sql_output.setFixedHeight(60)

        self.cost_comparison_label = QLabel("Cost Comparison:")
        self.cost_comparison_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.cost_comparison = QTextEdit(self)
        self.cost_comparison.setReadOnly(True)
        self.cost_comparison.setFixedHeight(60)

        self.grid_layout.addWidget(self.sql_output_label, 4, 0, 1, 1)
        self.grid_layout.addWidget(self.sql_output, 5, 0, 1, 3)
        self.grid_layout.addWidget(self.cost_comparison_label, 6, 0, 1, 1)
        self.grid_layout.addWidget(self.cost_comparison, 7, 0, 1, 3)

        # Section 4: Visualizations
        self.qep_graph_label = QLabel("Query Execution Plan (Graphical Tree):")
        self.qep_graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qep_graph_view = QGraphicsView(self)
        self.qep_graph_scene = QGraphicsScene(self)
        self.qep_graph_view.setScene(self.qep_graph_scene)

        self.aqp_graph_label = QLabel("Alternative Query Plan (Graphical Tree):")
        self.aqp_graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aqp_graph_view = QGraphicsView(self)
        self.aqp_graph_scene = QGraphicsScene(self)
        self.aqp_graph_view.setScene(self.aqp_graph_scene)

        self.qep_graph_view.setStyleSheet("border: 1px solid lightgrey; border-radius: 5px;")
        self.aqp_graph_view.setStyleSheet("border: 1px solid lightgrey; border-radius: 5px;")

        self.grid_layout.addWidget(self.qep_graph_label, 8, 0, 1, 2)
        self.grid_layout.addWidget(self.qep_graph_view, 9, 0, 1, 2)
        self.grid_layout.addWidget(self.aqp_graph_label, 8, 2, 1, 2)
        self.grid_layout.addWidget(self.aqp_graph_view, 9, 2, 1, 2)

        # Section 5: Tree Views
        self.qep_tree_label = QLabel("QEP Tree View:")
        self.qep_tree = QTreeWidget(self)
        self.qep_tree.setHeaderLabels(["Node ID", "Node Type", "Total Cost", "Details"])
        self.qep_tree.setFixedHeight(300)

        self.aqp_tree_label = QLabel("AQP Tree View:")
        self.aqp_tree = QTreeWidget(self)
        self.aqp_tree.setHeaderLabels(["Node ID", "Node Type", "Total Cost", "Details"])
        self.aqp_tree.setFixedHeight(300)

        self.qep_tree.setStyleSheet("border: 1px solid lightgrey; border-radius: 5px;")
        self.aqp_tree.setStyleSheet("border: 1px solid lightgrey; border-radius: 5px;")

        self.grid_layout.addWidget(self.qep_tree_label, 10, 0, 1, 1)
        self.grid_layout.addWidget(self.qep_tree, 11, 0, 1, 2)
        self.grid_layout.addWidget(self.aqp_tree_label, 10, 2, 1, 1)
        self.grid_layout.addWidget(self.aqp_tree, 11, 2, 1, 2)

        # Set stretch factors for dynamic resizing
        self.grid_layout.setRowStretch(1, 1)
        self.grid_layout.setRowStretch(5, 1)
        self.grid_layout.setRowStretch(9, 3)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 2)

        # Allow right clicking
        self.setup_tree_interaction()

    def populate_tree_widget(self, parent_item, plan):
        """
        Recursively populate a QTreeWidget with the QEP or AQP structure.

        :param parent_item: QTreeWidgetItem to which the current node will be added.
        :param plan: Dictionary representing the QEP or AQP node.
        """
        # Extract Node Type, Total Cost, and Node ID
        node_type = plan.get("Node Type", "Unknown")
        total_cost = plan.get("Total Cost", "N/A")
        node_id = plan.get("Node ID", "N/A")  # Ensure Node ID is part of the JSON structure

        # Format details for additional attributes
        details = ", ".join(f"{key}: {value}" for key, value in plan.items()
                            if key not in ("Node Type", "Plans", "Total Cost", "Node ID"))

        # Create current node with Node Type, Total Cost, and Node ID
        current_item = QTreeWidgetItem(parent_item, [f"{node_id}", node_type, f"{total_cost}", details])

        # Store node ID in UserRole to track modifications at the backend
        if node_id != "N/A":
            current_item.setData(0, Qt.ItemDataRole.UserRole, node_id)

        # Recursively add child nodes
        for child_plan in plan.get("Plans", []):
            self.populate_tree_widget(current_item, child_plan)

    def generate_qep(self):
        query = self.query_input.toPlainText().strip()

        if not query:
            self.display_message("Error: Please enter a SQL query.")
            return

        try:
            self.modified_nodes = {}  # Reset any previous modifications
            self.qep_tree.clear()  # Clear previous QEP tree view
            self.aqp_tree.clear()  # Clear previous AQP tree view
            self.qep_graph_scene.clear()  # Clear the previous QEP graph
            self.aqp_graph_scene.clear()  # Clear the previous AQP graph
            
            # Clear the text output areas
            self.sql_output.clear()  # Clear the modified SQL query output
            self.cost_comparison.clear()  # Clear the cost comparison output

            # Retrieve the QEP for the original query
            qep = self.whatif.retrieve_qep(query)

            # Populate the QEP tree view with the new QEP
            root_item = QTreeWidgetItem(self.qep_tree, ["Root", "Query Execution Plan"])
            self.populate_tree_widget(root_item, qep["Plan"])
            self.qep_tree.expandAll()

            # Render the QEP as a graphical tree
            self.render_qep_graph(qep["Plan"])

            # Enable the modify button since a valid QEP is generated
            self.modify_qep_button.setEnabled(True)

        except Exception as e:
            self.display_message(f"Error generating QEP: {e}")

    def render_qep_graph(self, plan):
        """
        Render the QEP as a graphical tree using Graphviz and display it in the GUI.
        """
        graph = Digraph(format="png")
        self.add_plan_to_graph(graph, plan)  # Helper function to populate the graph

        graph_path = "qep_graph"
        graph.render(graph_path, cleanup=True)  # Save the graph as an image

        # Display the graph in the QGraphicsView
        pixmap = QPixmap(f"{graph_path}.png")
        self.qep_graph_scene.clear()
        self.qep_graph_scene.addPixmap(pixmap)
        self.qep_graph_view.setScene(self.qep_graph_scene)

    def render_aqp_graph(self, plan):
        """
        Render the AQP.
        """
        graph = Digraph(format="png")
        self.add_plan_to_graph(graph, plan)  # Reuse the helper function from QEP rendering

        graph_path = "aqp_graph"
        graph.render(graph_path, cleanup=True)  # Save the graph as an image

        # Display the graph in the QGraphicsView
        pixmap = QPixmap(f"{graph_path}.png")
        self.aqp_graph_scene.clear()
        self.aqp_graph_scene.addPixmap(pixmap)
        self.aqp_graph_view.setScene(self.aqp_graph_scene)

    def add_plan_to_graph(self, graph, node, parent_id=None, node_id=0):
        """
        Recursively add nodes to the Graphviz graph for the QEP.
        Ensures that the Node ID is consistent in both the graph and the tree.
        """
        # Use the node's actual ID from the QEP/AQP structure for consistency
        node_label = f"Node {node.get('Node ID', node_id)}: {node.get('Node Type', 'Unknown')}\nCost: {node.get('Total Cost', 'N/A')}"
        current_id = str(node.get('Node ID', node_id))  # Ensure we use the actual Node ID from the plan

        # Create Graphviz node
        graph.node(current_id, label=node_label)

        if parent_id is not None:
            graph.edge(parent_id, current_id)

        # Recursively add child nodes
        for i, child in enumerate(node.get("Plans", [])):
            self.add_plan_to_graph(graph, child, current_id, node_id=(node_id * 10 + i + 1))

    def setup_tree_interaction(self):
        """
        Add interactivity to the QEP Tree (e.g., right-click to modify nodes).
        """
        self.qep_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.qep_tree.customContextMenuRequested.connect(self.open_context_menu)

    def open_context_menu(self, position):
        """
        Show context menu to allow node-specific modifications based on node type.
        """
        item = self.qep_tree.itemAt(position)
        if item:
            # Create the context menu
            menu = QMenu()

            # Get the node type from the selected item
            node_type = item.text(1)  # Node Type is in the second column

            # Depending on the node type, offer different modification options
            if "Scan" in node_type:  # If it's a scan node
                force_index = QAction("Force Index Scan", self)
                force_seq = QAction("Force Sequential Scan", self)
                # force_bitmap = QAction("Force Bitmap Index Scan", self)
                # not implmenting force bitmap index scan

                # Connect actions to modify_node
                force_index.triggered.connect(lambda: self.modify_node(item, "Index Scan"))
                force_seq.triggered.connect(lambda: self.modify_node(item, "Seq Scan"))

                # Add actions for scan types
                menu.addAction(force_index)
                menu.addAction(force_seq)

            elif "Join" or "Nested" in node_type:  # If it's a join node
                force_hash = QAction("Force Hash Join", self)
                force_merge = QAction("Force Merge Join", self)
                force_nestloop = QAction("Force Nested Loop", self)

                # Connect actions to modify_node
                force_hash.triggered.connect(lambda: self.modify_node(item, "Hash Join"))
                force_merge.triggered.connect(lambda: self.modify_node(item, "Merge Join"))
                force_nestloop.triggered.connect(lambda: self.modify_node(item, "Nested Loop"))

                # Add actions for join types
                menu.addAction(force_hash)
                menu.addAction(force_merge)
                menu.addAction(force_nestloop)

            # Show the menu
            menu.exec(self.qep_tree.viewport().mapToGlobal(position))

    def modify_node(self, item, modification_type):
        """
        Modify the selected node in the QEP tree and prepare the modification for backend.
        """
        # Update the UI to reflect the modification
        item.setText(0, f"{modification_type} (Modified)")  # This updates the tree node UI

        # Capture node information for backend
        node_id = item.data(0, Qt.ItemDataRole.UserRole)  # Assume node ID is stored in UserRole
        if not hasattr(self, 'modified_nodes'):
            self.modified_nodes = {}  # Initialize a dictionary to track modifications

        # Ensure we're correctly modifying the node based on the modification type
        if modification_type in ["Index Scan", "Seq Scan"]:
            self.modified_nodes[node_id] = {"Scan Type": modification_type}  # Store the scan modification
        elif modification_type in ["Hash Join", "Merge Join", "Nested Loop"]:
            self.modified_nodes[node_id] = {"Node Type": modification_type}  # Store the join modification

        # Highlight the modified node in red for emphasis
        item.setForeground(1, QColor(255, 0, 0))  # Set the color of the Node Type column to red
        item.setForeground(3, QColor(255, 0, 0))  # Set the color of the Details column to red
        
        # Optionally, make the font bold for further emphasis
        font = item.font(1)
        font.setBold(True)
        item.setFont(1, font)

        font = item.font(3)
        font.setBold(True)
        item.setFont(3, font)

        # Notify user that the node was modified
        self.display_message(f"Node {node_id} modified to use {modification_type}")

    def generate_modified_query(self, original_query, modifications):
        """
        Generate a modified SQL query based on user-specified modifications.
        This version displays the modifications in a human-readable format.

        :param original_query: The original SQL query.
        :param modifications: The modifications applied to the query plan.
        :return: The modified SQL query in a natural language format.
        """
        modified_query = f"{original_query}\n-- Modified with:"
        
        for node_id, changes in modifications.items():
            for key, value in changes.items():
                if key == "Node Type":
                    modified_query += f"\n  - Node {node_id}: Changed Node Type to {value}"
                elif key == "Scan Type":
                    modified_query += f"\n  - Node {node_id}: Changed Scan Type to {value}"
                elif key == "Join Type":
                    modified_query += f"\n  - Node {node_id}: Changed Join Type to {value}"
        
        return modified_query

    def display_message(self, message):
        """
        Display error or status messages in the cost comparison panel.
        """
        self.cost_comparison.setPlainText(message)

    def modify_qep(self):
        """
        Perform the what-if analysis by modifying the QEP and generating the AQP.
        """
        query = self.query_input.toPlainText().strip()
        if not query:
            self.display_message("Error: Please enter a SQL query.")
            return

        try:
            # Check for modifications
            if not hasattr(self, 'modified_nodes') or not self.modified_nodes:
                self.display_message("No modifications to apply.")
                return

            # Retrieve QEP
            qep = self.whatif.retrieve_qep(query)

            # Apply modifications
            modified_qep = self.whatif.modify_qep(qep, self.modified_nodes)

            # Retrieve AQP for modified QEP
            aqp = self.whatif.retrieve_aqp(query, self.modified_nodes)

            # Render the AQP as a graphical tree
            self.render_aqp_graph(aqp["Plan"])

            # Populate the modified QEP tree view
            self.qep_tree.clear()
            qep_root_item = QTreeWidgetItem(self.qep_tree, ["Root", "Modified Query Execution Plan"])
            self.populate_tree_widget(qep_root_item, modified_qep["Plan"])
            self.qep_tree.expandAll()

            # Populate the AQP tree view
            self.aqp_tree.clear()  # Ensure the tree is cleared before populating
            aqp_root_item = QTreeWidgetItem(self.aqp_tree, ["Root", "Alternative Query Plan"])
            self.populate_tree_widget(aqp_root_item, aqp["Plan"])  # Use AQP data here
            self.aqp_tree.expandAll()

            # Display the modified SQL query and cost comparison
            modified_query = self.generate_modified_query(query, self.modified_nodes)
            self.sql_output.setPlainText(modified_query)

            cost_comparison = self.whatif.compare_costs(qep, aqp)
            self.cost_comparison.setPlainText(f"Original Cost: {cost_comparison['Original Cost']}\n"
                                            f"Modified Cost: {cost_comparison['Modified Cost']}\n"
                                            f"Cost Difference: {cost_comparison['Cost Difference']}")

        except Exception as e:
            self.display_message(f"Error modifying QEP: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QEPInterface()
    window.show()
    sys.exit(app.exec())
