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
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from whatif import WhatIfAnalysis
from preprocessing import Preprocessing

class QEPInterface(QWidget):
    """
    GUI to interactively visualize and modify Query Execution Plans (QEP).
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QEP and AQP What-If Analysis")
        self.setGeometry(100, 100, 1200, 800)

        # Layout for the entire window
        self.layout = QVBoxLayout(self)

        # SQL Query Input Area
        self.query_input_label = QLabel("Enter SQL Query:")
        self.query_input = QTextEdit(self)
        self.query_input.setPlaceholderText("Enter SQL query here")
        self.layout.addWidget(self.query_input_label)
        self.layout.addWidget(self.query_input)

        # Buttons for query execution and analysis
        self.run_query_button = QPushButton("Generate QEP", self)
        self.run_query_button.clicked.connect(self.generate_qep)

        self.modify_qep_button = QPushButton("Modify QEP (What-If Analysis)", self)
        self.modify_qep_button.clicked.connect(self.modify_qep)
        self.modify_qep_button.setEnabled(False)  # Disabled until QEP is generated

        self.layout.addWidget(self.run_query_button)
        self.layout.addWidget(self.modify_qep_button)

        # Tree to display the QEP
        self.qep_tree_label = QLabel("Query Execution Plan (QEP):")
        self.qep_tree = QTreeWidget(self)
        self.qep_tree.setHeaderLabel("QEP Nodes")
        self.layout.addWidget(self.qep_tree_label)
        self.layout.addWidget(self.qep_tree)

        # SQL Query and AQP Display
        self.sql_output_label = QLabel("Modified SQL Query:")
        self.sql_output = QTextEdit(self)
        self.sql_output.setReadOnly(True)
        self.layout.addWidget(self.sql_output_label)
        self.layout.addWidget(self.sql_output)

        # Cost Comparison Output
        self.cost_comparison_label = QLabel("Cost Comparison:")
        self.cost_comparison = QTextEdit(self)
        self.cost_comparison.setReadOnly(True)
        self.layout.addWidget(self.cost_comparison_label)
        self.layout.addWidget(self.cost_comparison)

    def generate_qep(self):
        """
        Generate the QEP for the SQL query entered by the user.
        """
        query = self.query_input.toPlainText().strip()
        if not query:
            self.display_message("Error: Please enter a SQL query.")
            return

        preprocessing = Preprocessing()
        if not preprocessing.validate_query(query):
            self.display_message("Error: Invalid SQL query.")
            return

        try:
            qep = preprocessing.preprocess_for_gui(query)
            self.qep_tree.clear()
            self.populate_tree(self.qep_tree, qep)
            self.modify_qep_button.setEnabled(True)
        except Exception as e:
            self.display_message(f"Error generating QEP: {e}")

    def populate_tree(self, tree_widget, qep_data):
        """
        Populate the QEP tree with the processed QEP data.
        """
        def add_node(parent, node_data):
            node_text = f"{node_data.get('Node Type', 'Unknown')}"
            node_item = QTreeWidgetItem(parent, [node_text])

            for key, value in node_data["Details"].items():
                QTreeWidgetItem(node_item, [f"{key}: {value}"])

            for child in node_data["Children"]:
                add_node(node_item, child)

        root = QTreeWidgetItem(tree_widget, ["Root Plan"])
        add_node(root, qep_data)
        tree_widget.addTopLevelItem(root)
        tree_widget.expandAll()

    def modify_qep(self):
        """
        Perform the what-if analysis by modifying the QEP and generating the AQP.
        """
        query = self.query_input.toPlainText().strip()
        if not query:
            self.display_message("Error: Please enter a SQL query.")
            return

        try:
            preprocessing = Preprocessing()
            qep = preprocessing.preprocess_for_gui(query)

            modifications = {"Node Type": "Merge Join"}  # Example: Force Merge Join
            whatif = WhatIfAnalysis()

            aqp = whatif.retrieve_aqp(query, modifications)

            self.qep_tree.clear()
            self.populate_tree(self.qep_tree, aqp["Plan"])

            cost_comparison = whatif.compare_costs(qep, aqp)
            self.cost_comparison.setPlainText(f"Original Cost: {cost_comparison['Original Cost']}\n"
                                              f"Modified Cost: {cost_comparison['Modified Cost']}\n"
                                              f"Cost Difference: {cost_comparison['Cost Difference']}")
        except Exception as e:
            self.display_message(f"Error modifying QEP: {e}")

    def display_message(self, message):
        """
        Display error or status messages.
        """
        self.cost_comparison.setPlainText(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QEPInterface()
    window.show()
    sys.exit(app.exec())
