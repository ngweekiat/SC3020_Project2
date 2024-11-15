"""
whatif.py
----------
Purpose:
    - Handles the logic for generating modified SQL queries and their corresponding AQPs (Alternative Query Plans) based on what-if questions.

Requirements:
    1. Accept as input:
        - The original SQL query.
        - User modifications to the QEP (e.g., changes in operators, join order).
    2. Generate:
        - The modified SQL query reflecting the user edits.
        - The modified QEP (AQP) using PostgreSQL's planner method configuration.
    3. Retrieve and compare:
        - The estimated cost of the AQP with the original QEP.
    4. Ensure generality:
        - Handle a wide variety of queries and database schemas.
        - Avoid hardcoding schema-specific or query-specific logic.
"""

import psycopg2
import os
from typing import Dict
import dotenv

dotenv.load_dotenv()


class WhatIfAnalysis:
    """
    What-If Analysis Tool for Query Execution Plans (QEPs).
    Handles modification of QEPs, SQL query generation, and cost comparisons.
    """

    def __init__(self):
        self.conn_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "tpch")
        }

    def connect_to_db(self):
        """
        Establishes a connection to the PostgreSQL database.
        """
        try:
            return psycopg2.connect(**self.conn_params)
        except psycopg2.OperationalError as e:
            raise ConnectionError(f"Database connection error: {e}")

    def retrieve_qep(self, query: str) -> Dict:
        """
        Retrieves the Query Execution Plan (QEP) for the given SQL query.

        :param query: The SQL query.
        :return: The QEP as a dictionary.
        """
        try:
            with self.connect_to_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
                    return cursor.fetchone()[0][0]
        except psycopg2.Error as e:
            raise RuntimeError(f"Error retrieving QEP: {e}")

    def modify_qep(self, original_qep: Dict, modifications: Dict) -> Dict:
        """
        Modifies the QEP based on user-specified changes.

        :param original_qep: Original QEP as a dictionary.
        :param modifications: Modifications to be applied (e.g., operator changes).
        :return: The modified QEP structure.
        """
        modified_qep = original_qep.copy()

        def apply_changes(node, changes):
            for key, value in changes.items():
                if key in node:
                    node[key] = value
            if "Plans" in node:
                for i, child in enumerate(node["Plans"]):
                    if i < len(changes.get("Children", [])):
                        apply_changes(child, changes["Children"][i])

        apply_changes(modified_qep["Plan"], modifications)
        return modified_qep

    def generate_modified_sql(self, original_sql: str, modifications: Dict) -> str:
        """
        Generates a modified SQL query based on the QEP modifications.

        :param original_sql: The original SQL query.
        :param modifications: Modifications made to the QEP.
        :return: The modified SQL query.
        """
        hints = {
            "Merge Join": "/*+ MergeJoin */",
            "Hash Join": "/*+ HashJoin */",
            "Nested Loop": "/*+ NestedLoop */"
        }

        hint = hints.get(modifications.get("Node Type", ""), "")
        return f"{original_sql} {hint}" if hint else original_sql

    def retrieve_aqp(self, modified_sql: str) -> Dict:
        """
        Retrieves the Alternative Query Plan (AQP) for the modified SQL query.

        :param modified_sql: The modified SQL query.
        :return: The AQP as a dictionary.
        """
        return self.retrieve_qep(modified_sql)

    def compare_costs(self, qep: Dict, aqp: Dict) -> Dict:
        """
        Compares the costs of the QEP and the AQP.

        :param qep: The original QEP.
        :param aqp: The modified AQP.
        :return: A dictionary containing cost comparison results.
        """
        original_cost = qep["Plan"].get("Total Cost", -1)
        modified_cost = aqp["Plan"].get("Total Cost", -1)
        return {
            "Original Cost": original_cost,
            "Modified Cost": modified_cost,
            "Cost Difference": modified_cost - original_cost
        }
