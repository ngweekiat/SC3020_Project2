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

        try:
            qep = self.whatif.retrieve_qep(query)
            self.qep_tree.clear()
            self.populate_tree(self.qep_tree, qep["Plan"])
            self.modify_qep_button.setEnabled(True)
        except Exception as e:
            self.display_message(f"Error generating QEP: {e}")

    def populate_tree(self, tree_widget, node_data):
        """
        Populate the QEP tree with the processed QEP data.
        """
        def add_node(parent, node_data):
            node_text = f"{node_data.get('Node Type', 'Unknown')} (Cost: {node_data.get('Total Cost', 'N/A')})"
            node_item = QTreeWidgetItem(parent, [node_text])

            for key, value in node_data.items():
                if isinstance(value, dict) or isinstance(value, list):
                    continue  # Skip nested structures for now
                QTreeWidgetItem(node_item, [f"{key}: {value}"])

            if "Plans" in node_data:
                for child in node_data["Plans"]:
                    add_node(node_item, child)

        root = QTreeWidgetItem(tree_widget, ["Root Plan"])
        add_node(root, node_data)
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
            modifications = {"Node Type": "Merge Join"}  # Example: Force Merge Join
            qep = self.whatif.retrieve_qep(query)
            aqp = self.whatif.retrieve_aqp(query, modifications)

            # Update QEP Tree with AQP
            self.qep_tree.clear()
            self.populate_tree(self.qep_tree, aqp["Plan"])

            # Generate the modified SQL query for display
            modified_query = self.generate_modified_query(query, modifications)
            self.sql_output.setPlainText(modified_query)

            # Display Cost Comparison
            cost_comparison = self.whatif.compare_costs(qep, aqp)
            self.cost_comparison.setPlainText(f"Original Cost: {cost_comparison['Original Cost']}\n"
                                              f"Modified Cost: {cost_comparison['Modified Cost']}\n"
                                              f"Cost Difference: {cost_comparison['Cost Difference']}")

        except Exception as e:
            self.display_message(f"Error modifying QEP: {e}")

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
        Display error or status messages.
        """
        self.cost_comparison.setPlainText(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QEPInterface()
    window.show()
    sys.exit(app.exec())
