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
import json

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

    def retrieve_qep(self, query: str) -> dict:
        """
        Retrieves the Query Execution Plan (QEP) for the given SQL query.
        Assigns unique IDs to nodes for tracking purposes.
        """
        try:
            with self.connect_to_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
                    qep = cursor.fetchone()[0][0]

                    # Assign unique node IDs recursively
                    def assign_node_ids(node, current_id=1):
                        node["Node ID"] = current_id
                        child_id = current_id * 10  # Increment child IDs systematically
                        for i, child in enumerate(node.get("Plans", [])):
                            assign_node_ids(child, child_id + i)

                    assign_node_ids(qep["Plan"])
                    return qep
        except psycopg2.Error as e:
            raise RuntimeError(f"Error retrieving QEP: {e}")




    def modify_qep(self, original_qep: Dict, modifications: Dict) -> Dict:
        modified_qep = original_qep.copy()

        # Ensure modifications for node 10 are added
        modifications[10] = {"Scan Type": "Index Scan"}  # Modify node 10 to use Index Scan

        # Apply modifications to the QEP recursively
        def apply_changes(node, modifications):
            node_id = node.get("Node ID")
            if node_id in modifications:
                modification = modifications[node_id]
                if "Scan Type" in modification:
                    node["Node Type"] = modification["Scan Type"]
                if "Node Type" in modification:
                    node["Node Type"] = modification["Node Type"]

        # Apply modifications to the QEP's root node
        apply_changes(modified_qep["Plan"], modifications)
        return modified_qep









    def logical_transformations(self, query: str, modifications: Dict) -> str:
        """
        Apply transformations to the query based on logical heuristics.
        """
        transformed_query = query
        if "Push Selections" in modifications:
            # Example: Push selection conditions closer to base tables
            transformed_query = self.push_selections(query)
        if "Reorder Joins" in modifications:
            # Example: Reorder joins based on estimated cardinalities
            transformed_query = self.reorder_joins(query, modifications["Join Order"])
        return transformed_query



    def apply_planner_settings(self, modifications: Dict) -> str:
        """
        Apply planner settings to enforce specific behaviors for the AQP, including scan types.
        """
        settings = []
        for node_id, changes in modifications.items():
            # Apply scan type changes if any
            if "Scan Type" in changes:
                scan_type = changes["Scan Type"]
                if scan_type == "Index Scan":
                    settings.append("SET enable_seqscan = OFF; SET enable_indexscan = ON;")
                elif scan_type == "Seq Scan":
                    settings.append("SET enable_seqscan = ON; SET enable_indexscan = OFF;")

            # Example: Apply node type changes (joins)
            if "Node Type" in changes:
                settings.append(self.get_operator_setting(changes["Node Type"]))

        # Combine settings into a single query
        planner_query = " ".join(settings)
        print(f"Generated planner settings: {planner_query}")  # Debug print
        return planner_query





    def get_operator_setting(self, operator_type: str) -> str:
        """
        Map operator types to PostgreSQL settings.
        """
        mapping = {
            "Merge Join": "SET enable_hashjoin = OFF; SET enable_mergejoin = ON;",
            "Hash Join": "SET enable_mergejoin = OFF; SET enable_hashjoin = ON;",
            "Nested Loop": "SET enable_mergejoin = OFF; SET enable_hashjoin = OFF; SET enable_nestloop = ON;"
        }
        return mapping.get(operator_type, "")



    def retrieve_aqp(self, original_sql: str, modifications: Dict) -> Dict:
        """
        Retrieves the Alternative Query Plan (AQP) for the modified SQL query.
        Applies planner settings to enforce desired behavior.
        """
        planner_settings = self.apply_planner_settings(modifications)
        print(f"Applied planner settings for AQP: {planner_settings}")

        try:
            with self.connect_to_db() as conn:
                with conn.cursor() as cursor:
                    if planner_settings:
                        cursor.execute(planner_settings)  # Apply planner settings

                    cursor.execute(f"EXPLAIN (FORMAT JSON) {original_sql}")
                    aqp = cursor.fetchone()[0][0]

                    # Assign unique IDs to AQP nodes recursively
                    def assign_node_ids(node, current_id=1):
                        node["Node ID"] = current_id
                        child_id = current_id * 10
                        for i, child in enumerate(node.get("Plans", [])):
                            assign_node_ids(child, child_id + i)

                    assign_node_ids(aqp["Plan"])
                    return aqp

        except psycopg2.Error as e:
            raise RuntimeError(f"Error retrieving AQP: {e}")






    def compare_costs(self, qep: Dict, aqp: Dict) -> Dict:
        """
        Compare costs of the QEP and AQP with a detailed breakdown.
        """
        import json
        print("QEP COMPARE COST DEBUG: " + json.dumps(qep, indent=4))  # Pretty-print with indentation
        print("AQP COMPARE COST DEBUG: " + json.dumps(aqp, indent=4))  # Pretty-print with indentation

        original_cost = float(qep["Plan"].get("Total Cost", -1))
        modified_cost = float(aqp["Plan"].get("Total Cost", -1))

        # Ensure original cost is valid
        if original_cost == -1 or modified_cost == -1:
            raise ValueError("Failed to retrieve cost from QEP or AQP.")
        
        # Debugging prints
        print(f"Original QEP Cost: {original_cost}")
        print(f"Modified AQP Cost: {modified_cost}")

        return {
            "Original Cost": original_cost,
            "Modified Cost": modified_cost,
            "Cost Difference": modified_cost - original_cost
        }


