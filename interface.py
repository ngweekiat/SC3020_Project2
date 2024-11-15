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

