"""
interface.py
-------------
Purpose:
    - Manages the graphical user interface (GUI) for the application.

Requirements:
    1. Allow users to:
        - Choose a database schema (e.g., TPC-H).
        - Input SQL queries via a Query panel.
        - View the QEP (Query Execution Plan) in a visual tree format.
        - Interactively edit the QEP for posing what-if questions (e.g., changing operators or join orders).
        - View the modified SQL query generated from user edits.
        - Compare the costs of the modified query plan (AQP) with the original QEP.
    2. Provide a user-friendly interface with:
        - A Query Input panel for entering SQL queries.
        - A QEP Visualization and Editing panel.
        - A panel for displaying the modified SQL query and cost comparison.
"""


from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QTreeWidgetItem, QHeaderView
import pyqtgraph as pg
from preprocessing import Preprocessing
from whatif import WhatIfAnalysis

colorGradient = ["#DDF4F6", "#BCF1F5", "#99EDF3", "#77ECF5", "#47E4F0", "#0CD4E3", "#06C0CE", "#04A6B2", "#01818A",
                 "#005E65", "#004146"]


class MainUI(QtWidgets.QMainWindow):
    """
    Main GUI for the What-If Analysis Tool
    """

    def __init__(self, login_details, db_list):
        super().__init__()
        self.login_details = login_details
        self.db_list = db_list
        self.setWindowTitle("What-If Analysis of Query Plans")
        self.resize(1350, 900)
        self.initUI()

    def initUI(self):
        """
        Initialize the main user interface components.
        """
        self.centralWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralWidget)

        # Layouts
        main_layout = QtWidgets.QVBoxLayout(self.centralWidget)
        query_layout = QtWidgets.QHBoxLayout()
        plan_layout = QtWidgets.QHBoxLayout()
        comparison_layout = QtWidgets.QVBoxLayout()

        # Query Input Area
        self.queryInput = QtWidgets.QPlainTextEdit(self)
        self.queryInput.setPlaceholderText("Enter your SQL query here...")
        self.queryInput.setStyleSheet("font: 12px; color: #018076;")
        query_layout.addWidget(self.queryInput)

        # Execute Query Button
        self.executeButton = QtWidgets.QPushButton("Execute Query", self)
        self.executeButton.setStyleSheet("background-color: #004146; color: white; font: 14px;")
        self.executeButton.clicked.connect(self.execute_query)
        query_layout.addWidget(self.executeButton)

        # Add Query Layout
        main_layout.addLayout(query_layout)

        # QEP Visualization Panel
        self.qepTree = QtWidgets.QTreeWidget(self)
        self.qepTree.setHeaderLabel("Query Execution Plan (QEP)")
        self.qepTree.setStyleSheet("font: 12px; color: #018076;")
        plan_layout.addWidget(self.qepTree)

        # Modified QEP Panel
        self.modifiedQEPTree = QtWidgets.QTreeWidget(self)
        self.modifiedQEPTree.setHeaderLabel("Modified Query Execution Plan (QEP)")
        self.modifiedQEPTree.setStyleSheet("font: 12px; color: #018076;")
        plan_layout.addWidget(self.modifiedQEPTree)

        # Add Plan Layout
        main_layout.addLayout(plan_layout)

        # Cost Comparison Panel
        self.graphWindow = pg.PlotWidget(self)
        self.graphWindow.setBackground("#ffffff")
        self.graphWindow.setStyleSheet("font: 12px; color: #018076;")
        comparison_layout.addWidget(self.graphWindow)

        # Add Comparison Layout
        main_layout.addLayout(comparison_layout)

    def execute_query(self):
        """
        Execute the SQL query and display the QEP.
        """
        query = self.queryInput.toPlainText()
        preprocessing = Preprocessing()
        whatif = WhatIfAnalysis()

        # Retrieve QEP
        try:
            qep = preprocessing.preprocess_qep(query)
            self.populate_tree(self.qepTree, qep)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to retrieve QEP: {e}")

        # Enable interactive modifications
        self.qepTree.itemDoubleClicked.connect(self.modify_qep)

    def modify_qep(self, item):
        """
        Modify the QEP based on user interaction.
        """
        modifications = {"Node Type": "Merge Join"}  # Example modification
        whatif = WhatIfAnalysis()

        # Generate modified QEP
        modified_qep = whatif.modify_qep(item.data(0, QtCore.Qt.ItemDataRole.UserRole), modifications)
        self.populate_tree(self.modifiedQEPTree, modified_qep)

        # Generate AQP and compare costs
        modified_sql = whatif.generate_modified_sql(self.queryInput.toPlainText(), modifications)
        aqp = whatif.retrieve_aqp(modified_sql)
        costs = whatif.compare_costs(modified_qep, aqp)

        self.plot_cost_comparison(costs)

    def populate_tree(self, tree_widget, qep_data):
        """
        Populate the QEP tree widget with QEP data.
        """
        tree_widget.clear()

        def add_items(parent, data):
            for key, value in data.items():
                item = QTreeWidgetItem(parent, [f"{key}: {value}"])
                if isinstance(value, dict):
                    add_items(item, value)

        root = QTreeWidgetItem(tree_widget, ["Root"])
        add_items(root, qep_data)
        tree_widget.addTopLevelItem(root)

    def plot_cost_comparison(self, costs):
        """
        Plot the cost comparison between QEP and AQPs.
        """
        self.graphWindow.clear()

        labels = ["QEP", "AQP"]
        values = [costs["Original Cost"], costs["Modified Cost"]]
        bar_graphs = pg.BarGraphItem(x=[0, 1], height=values, width=0.6, brush="blue")
        self.graphWindow.addItem(bar_graphs)