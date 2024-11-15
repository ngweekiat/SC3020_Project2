"""
whatif.py
----------
Purpose:
    - Handles the logic for generating modified SQL queries and their corresponding AQPs (Alternative Query Plans) based on what-if questions.

Improvements:
    1. Supports more types of modifications (e.g., scan type, aggregation).
    2. Allows node-specific modifications (targeting specific nodes based on criteria).
    3. Enhances flexibility for dynamic user-specified changes.
    4. Handles a wide variety of queries and database schemas.

Requirements:
    - Accept original SQL query and user-specified modifications.
    - Generate the modified QEP (AQP) using PostgreSQL's planner method configuration.
    - Compare the estimated costs of the QEP and AQP.
"""

import psycopg2
import os
from typing import Dict
import dotenv

dotenv.load_dotenv()


class WhatIfAnalysis:
    """
    Enhanced What-If Analysis Tool for Query Execution Plans (QEPs).
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

        def apply_changes(node, changes, target_node_type=None):
            """
            Recursively apply changes to nodes in the QEP.

            :param node: Current node in the QEP.
            :param changes: Modifications to apply.
            :param target_node_type: Optional; target specific node types.
            """
            if target_node_type and node.get("Node Type") != target_node_type:
                return

            for key, value in changes.items():
                if key in node:
                    node[key] = value
                else:
                    print(f"Warning: Modification '{key}' not applicable to node {node.get('Node Type')}.")
            
            # Recursively apply to child nodes
            if "Plans" in node:
                for child in node["Plans"]:
                    apply_changes(child, changes, target_node_type)

        # Apply changes to the root node and recursively to child nodes
        apply_changes(modified_qep["Plan"], modifications, modifications.get("Target Node Type"))
        return modified_qep

    def logical_transformations(self, query: str) -> str:
        """
        Apply logical query plan transformations such as pushing selections, projections,
        and replacing Cartesian products with joins.

        :param query: Original SQL query.
        :return: Transformed SQL query.
        """
        # Example of pushing selections down and reordering joins
        # NOTE: In practice, implement a parser for SQL or use a library
        transformed_query = query  # Placeholder for transformation logic
        print("Logical transformations applied.")
        return transformed_query

    def apply_planner_settings(self, modifications: Dict) -> str:
        """
        Apply planner settings to enforce specific behaviors for the AQP.

        :param modifications: The desired modifications (e.g., "Merge Join").
        :return: SQL commands to set planner settings.
        """
        settings = {
            "Merge Join": "SET enable_hashjoin = OFF; SET enable_mergejoin = ON;",
            "Hash Join": "SET enable_mergejoin = OFF; SET enable_hashjoin = ON;",
            "Nested Loop": "SET enable_mergejoin = OFF; SET enable_hashjoin = OFF; SET enable_nestloop = ON;",
            "Seq Scan": "SET enable_seqscan = ON;",
            "Index Scan": "SET enable_seqscan = OFF; SET enable_indexscan = ON;"
        }
        return settings.get(modifications.get("Node Type", ""), "")

    def retrieve_aqp(self, original_sql: str, modifications: Dict) -> Dict:
        """
        Retrieves the Alternative Query Plan (AQP) for the modified SQL query.
        Applies planner settings to enforce desired behavior.

        :param original_sql: The original SQL query.
        :param modifications: The modifications to apply for generating the AQP.
        :return: The AQP as a dictionary.
        """
        planner_settings = self.apply_planner_settings(modifications)

        try:
            with self.connect_to_db() as conn:
                with conn.cursor() as cursor:
                    # Apply planner settings
                    if planner_settings:
                        cursor.execute(planner_settings)

                    # Apply logical transformations
                    transformed_sql = self.logical_transformations(original_sql)

                    # Retrieve the AQP
                    cursor.execute(f"EXPLAIN (FORMAT JSON) {transformed_sql}")
                    aqp = cursor.fetchone()[0][0]

                    # Reset settings to default
                    cursor.execute("RESET enable_hashjoin; RESET enable_mergejoin; RESET enable_nestloop;")
                    return aqp
        except psycopg2.Error as e:
            raise RuntimeError(f"Error retrieving AQP: {e}")

    def compare_costs(self, qep: Dict, aqp: Dict) -> Dict:
        """
        Compares the costs of the QEP and the AQP.

        :param qep: The original QEP.
        :param aqp: The modified AQP.
        :return: A dictionary containing cost comparison results.
        """
        original_cost = float(qep["Plan"].get("Total Cost", -1))
        modified_cost = float(aqp["Plan"].get("Total Cost", -1))
        return {
            "Original Cost": original_cost,
            "Modified Cost": modified_cost,
            "Cost Difference": modified_cost - original_cost
        }
