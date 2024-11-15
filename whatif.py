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

    def retrieve_qep(self, query: str, modifications: dict = None) -> dict:
        """
        Retrieves the Query Execution Plan (QEP) for the given SQL query.
        Optionally applies modifications (e.g., planner settings).
        """
        try:
            with self.connect_to_db() as conn:
                with conn.cursor() as cursor:
                    # Apply modifications if provided
                    if modifications:
                        planner_settings = self.apply_planner_settings(modifications)
                        cursor.execute(planner_settings)

                    # Retrieve QEP
                    cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
                    qep = cursor.fetchone()[0][0]
                    
                    # Debug: Print the retrieved QEP for inspection
                    print("Retrieved QEP:", qep)  # Debug statement

                    return qep
        except psycopg2.Error as e:
            raise RuntimeError(f"Error retrieving QEP: {e}")




    def modify_qep(self, original_qep: Dict, modifications: Dict) -> Dict:
        """
        Modifies the QEP based on user-specified changes (scan type, node type, etc.).
        """
        modified_qep = original_qep.copy()

        def apply_changes(node, changes, target_node_type=None):
            """
            Apply changes to nodes in the QEP recursively with stricter matching.
            """
            if target_node_type and node.get("Node Type") != target_node_type:
                return
            
            # Match additional attributes if specified
            if "Relation Name" in changes and node.get("Relation Name") != changes["Relation Name"]:
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

        # Apply scan type modifications
        if "Scan Type" in modifications:
            scan_type = modifications["Scan Type"]
            if scan_type == "Index Scan":
                print("Forcing Index Scan...")
                apply_changes(modified_qep["Plan"], {"Node Type": "Index Scan"})
            elif scan_type == "Seq Scan":
                print("Forcing Sequential Scan...")
                apply_changes(modified_qep["Plan"], {"Node Type": "Seq Scan"})

        # Apply other modifications like join type changes
        if "Node Type" in modifications:
            print(f"Changing Node Type to: {modifications['Node Type']}")
            apply_changes(modified_qep["Plan"], {"Node Type": modifications["Node Type"]})

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
        
        # Apply node type modifications (join type, etc.)
        if "Node Type" in modifications:
            settings.append(self.get_operator_setting(modifications["Node Type"]))
        
        # Apply scan type modifications (e.g., Index Scan, Seq Scan)
        if "Scan Type" in modifications:
            scan_type = modifications["Scan Type"]
            if scan_type == "Index Scan":
                settings.append("SET enable_seqscan = OFF; SET enable_indexscan = ON;")
            elif scan_type == "Seq Scan":
                settings.append("SET enable_seqscan = ON; SET enable_indexscan = OFF;")
        
        # Handle other planner settings like Join Order, Parallelism
        if "Join Order" in modifications:
            settings.append(f"SET join_collapse_limit = {len(modifications['Join Order'])};")
        if "Parallelism" in modifications:
            settings.append("SET max_parallel_workers_per_gather = 0;")
        
        # Return the settings as a single query string
        planner_query = " ".join(settings)
        print(f"Planner settings applied: {planner_query}")  # Debug print to verify applied settings
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
        print(f"Applied planner settings for AQP: {planner_settings}")  # Debug print

        try:
            with self.connect_to_db() as conn:
                with conn.cursor() as cursor:
                    # Apply planner settings BEFORE executing EXPLAIN for AQP
                    if planner_settings:
                        cursor.execute(planner_settings)

                    # Log modifications for debugging
                    print(f"Modified SQL for AQP: {original_sql}")  # Debug print

                    # Retrieve AQP with EXPLAIN
                    cursor.execute(f"EXPLAIN (FORMAT JSON) {original_sql}")
                    aqp = cursor.fetchone()[0][0]

                    # Return AQP and keep settings applied for comparison
                    return aqp

        except psycopg2.Error as e:
            print(f"Error retrieving AQP: {e}")  # Debug print
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


