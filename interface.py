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
from PyQt6.QtWidgets import QApplication, QWidget, QScrollArea, QGridLayout, QTreeWidgetItemIterator, QLineEdit, QVBoxLayout, QPushButton, QTextEdit, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from whatif import WhatIfAnalysis
from PyQt6.QtWidgets import QComboBox
from graphviz import Digraph
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene


class QEPInterface(QWidget):
    """
    GUI to interactively visualize and modify Query Execution Plans (QEP).
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QEP and AQP What-If Analysis")
        self.setGeometry(100, 100, 1200, 800)

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
        self.query_input.setFixedHeight(100)

        self.grid_layout.addWidget(self.query_input_label, 0, 0, 1, 3)
        self.grid_layout.addWidget(self.query_input, 1, 0, 1, 3)

        # Section 2: Execution Options
        self.planner_settings_label = QLabel("Select Planner Settings:")
        self.planner_settings_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.planner_settings = QComboBox(self)
        self.planner_settings.addItems([
            "Default",
            "Force Hash Join",
            "Force Merge Join",
            "Force Nested Loop",
            "Force Index Scan",
            "Force Seq Scan"
        ])
        self.planner_settings.setFixedHeight(30)

        self.run_query_button = QPushButton("Generate QEP")
        self.run_query_button.clicked.connect(self.generate_qep)

        self.modify_qep_button = QPushButton("Modify QEP (What-If Analysis)")
        self.modify_qep_button.clicked.connect(self.modify_qep)
        self.modify_qep_button.setEnabled(False)

        self.grid_layout.addWidget(self.planner_settings_label, 2, 0, 1, 1)
        self.grid_layout.addWidget(self.planner_settings, 2, 1, 1, 2)
        self.grid_layout.addWidget(self.run_query_button, 3, 0, 1, 1)
        self.grid_layout.addWidget(self.modify_qep_button, 3, 1, 1, 1)

        # Section 3: Outputs
        self.sql_output_label = QLabel("Modified SQL Query:")
        self.sql_output_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.sql_output = QTextEdit(self)
        self.sql_output.setReadOnly(True)
        self.sql_output.setFixedHeight(100)

        self.cost_comparison_label = QLabel("Cost Comparison:")
        self.cost_comparison_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.cost_comparison = QTextEdit(self)
        self.cost_comparison.setReadOnly(True)
        self.cost_comparison.setFixedHeight(100)

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

        self.grid_layout.addWidget(self.qep_graph_label, 8, 0, 1, 2)
        self.grid_layout.addWidget(self.qep_graph_view, 9, 0, 1, 2)
        self.grid_layout.addWidget(self.aqp_graph_label, 8, 2, 1, 2)
        self.grid_layout.addWidget(self.aqp_graph_view, 9, 2, 1, 2)

        # Section 5: Tree Views
        self.qep_tree_label = QLabel("QEP Tree View:")
        self.qep_tree = QTreeWidget(self)
        self.qep_tree.setHeaderLabels(["Node Type", "Total Cost", "Details"])

        self.aqp_tree_label = QLabel("AQP Tree View:")
        self.aqp_tree = QTreeWidget(self)
        self.aqp_tree.setHeaderLabels(["Node Type", "Total Cost", "Details"])

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





    def populate_tree_widget(self, parent_item, plan):
        """
        Recursively populate a QTreeWidget with the QEP or AQP structure.

        :param parent_item: QTreeWidgetItem to which the current node will be added.
        :param plan: Dictionary representing the QEP or AQP node.
        """
        # Extract Node Type and Total Cost
        node_type = plan.get("Node Type", "Unknown")
        total_cost = plan.get("Total Cost", "N/A")
        
        # Format details for additional attributes
        details = ", ".join(f"{key}: {value}" for key, value in plan.items() 
                            if key not in ("Node Type", "Plans", "Total Cost"))
        
        # Create current node with Node Type and Total Cost
        current_item = QTreeWidgetItem(parent_item, [node_type, f"Cost: {total_cost}", details])

        # Recursively add child nodes
        for child_plan in plan.get("Plans", []):
            self.populate_tree_widget(current_item, child_plan)



    def generate_qep(self):
        """
        Generate the QEP for the SQL query entered by the user.
        """
        query = self.query_input.toPlainText().strip()
        if not query:
            self.display_message("Error: Please enter a SQL query.")
            return

        try:
            # Retrieve selected planner settings
            selected_setting = self.planner_settings.currentText()
            modifications = {}
            if "Force" in selected_setting:
                # Parse setting to apply planner configurations
                node_type = selected_setting.split()[-2]
                modifications = {"Node Type": node_type}

            # Call retrieve_qep with modifications
            qep = self.whatif.retrieve_qep(query, modifications)

            # Clear and populate the QEP tree view
            self.qep_tree.clear()
            root_item = QTreeWidgetItem(self.qep_tree, ["Root", "Query Execution Plan"])
            self.populate_tree_widget(root_item, qep["Plan"])
            self.qep_tree.expandAll()

            # Render the QEP as a graphical tree
            self.render_qep_graph(qep["Plan"])
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
        Render the AQP as a graphical tree using Graphviz and display it in the GUI.
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
        """
        node_label = f"{node.get('Node Type', 'Unknown')}\nCost: {node.get('Total Cost', 'N/A')}"
        current_id = str(node_id)
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
        Show context menu to allow node-specific modifications.
        """
        item = self.qep_tree.itemAt(position)
        if item:
            menu = QMenu()
            force_hash = QAction("Force Hash Join", self)
            force_merge = QAction("Force Merge Join", self)
            force_nestloop = QAction("Force Nested Loop", self)

            force_hash.triggered.connect(lambda: self.modify_node(item, "Hash Join"))
            force_merge.triggered.connect(lambda: self.modify_node(item, "Merge Join"))
            force_nestloop.triggered.connect(lambda: self.modify_node(item, "Nested Loop"))

            menu.addAction(force_hash)
            menu.addAction(force_merge)
            menu.addAction(force_nestloop)
            menu.exec(self.qep_tree.viewport().mapToGlobal(position))

    def modify_node(self, item, new_operator):
        """
        Modify the selected node in the QEP tree.
        """
        item.setText(0, f"{new_operator} (Modified)")
        # Store the modification for backend processing
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.modified_nodes[node_id] = {"Node Type": new_operator}



    def generate_modified_query(self, original_query, modifications):
        """
        Generate a modified SQL query based on user-specified modifications.
        This is a placeholder for logic to apply query transformations.

        :param original_query: The original SQL query.
        :param modifications: The modifications applied to the query plan.
        :return: The modified SQL query.
        """
        # For demonstration, we'll append comments indicating modifications
        modified_query = f"{original_query}\n-- Modified with: {modifications}"
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
            # Retrieve selected planner setting
            selected_setting = self.planner_settings.currentText()
            modifications = {}

            # Handle scan type modification
            if "Force Index Scan" in selected_setting:
                modifications["Scan Type"] = "Index Scan"
            elif "Force Seq Scan" in selected_setting:
                modifications["Scan Type"] = "Seq Scan"

            # Handle node type modification (e.g., Hash Join, Nested Loop)
            if "Force Hash Join" in selected_setting:
                modifications["Node Type"] = "Hash Join"
            elif "Force Merge Join" in selected_setting:
                modifications["Node Type"] = "Merge Join"
            elif "Force Nested Loop" in selected_setting:
                modifications["Node Type"] = "Nested Loop"

            # Retrieve QEP and AQP
            qep = self.whatif.retrieve_qep(query)
            aqp = self.whatif.retrieve_aqp(query, modifications)

            # Render the AQP as a graphical tree
            self.render_aqp_graph(aqp["Plan"])


            # Populate the QEP tree view
            self.qep_tree.clear()
            qep_root_item = QTreeWidgetItem(self.qep_tree, ["Root", "Query Execution Plan"])
            self.populate_tree_widget(qep_root_item, qep["Plan"])
            self.qep_tree.expandAll()

            # Populate the AQP tree view
            self.aqp_tree.clear()
            aqp_root_item = QTreeWidgetItem(self.aqp_tree, ["Root", "Alternative Query Plan"])
            self.populate_tree_widget(aqp_root_item, aqp["Plan"])
            self.aqp_tree.expandAll()

            # Display the modified SQL query and cost comparison
            modified_query = self.generate_modified_query(query, modifications)
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
