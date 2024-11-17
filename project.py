import sys
from PyQt6.QtWidgets import QApplication
from interface import QEPInterface
from preprocessing import Preprocessing
from whatif import WhatIfAnalysis

class Project:
    def __init__(self):
        # Initialize the preprocessing and what-if analysis modules
        self.preprocessing = Preprocessing()
        self.whatif_analysis = WhatIfAnalysis()

        # Validate TPC-H Schema
        self.validate_tpch_schema()

    def validate_tpch_schema(self):
        """
        Ensure that the database is correctly set up.
        """
        print("Validating TPC-H schema...")
        if self.preprocessing.validate_tpch_schema():
            print("TPC-H schema validation successful.")
        else:
            print("Error: TPC-H schema validation failed. Please ensure all required tables are present.")
            sys.exit(1)

    def run(self):
        """
        Launch the GUI.
        """
        # Create the PyQt application
        app = QApplication(sys.argv)

        # Initialize the GUI with integrated functionality
        gui = QEPInterface()

        # Inject backend dependencies into the GUI
        gui.whatif = self.whatif_analysis  # Set What-If analysis module in GUI
        gui.preprocessing = self.preprocessing  # Set Preprocessing module for the GUI
        gui.show()

        # Start the application loop
        sys.exit(app.exec())

if __name__ == "__main__":
    # Instantiate and run the project
    project = Project()
    project.run()
