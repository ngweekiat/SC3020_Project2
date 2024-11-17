import sys
from PyQt6.QtWidgets import QApplication
from interface import QEPInterface
from preprocessing import Preprocessing
from whatif import WhatIfAnalysis

class Project:
    def __init__(self):
        self.preprocessing = Preprocessing()
        self.whatif_analysis = WhatIfAnalysis()

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
        app = QApplication(sys.argv)

        gui = QEPInterface()

        gui.whatif = self.whatif_analysis 
        gui.preprocessing = self.preprocessing 
        gui.show()

        sys.exit(app.exec())

if __name__ == "__main__":
    project = Project()
    project.run()
