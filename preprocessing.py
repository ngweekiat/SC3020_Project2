import psycopg2
import os
from typing import List, Dict, Optional
import dotenv

dotenv.load_dotenv()


class Preprocessing:
    def __init__(self):
        self.conn_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "tpch")
        }

    def connect_to_db(self, database: Optional[str] = None):
        params = self.conn_params.copy()
        if database:
            params["database"] = database

        try:
            conn = psycopg2.connect(**params)
            return conn
        except psycopg2.OperationalError as e:
            raise ConnectionError(f"Error connecting to the database: {e}")

    def validate_query(self, query: str) -> bool:
        try:
            conn = self.connect_to_db()
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN {query}")
            conn.close()
            return True
        except psycopg2.Error:
            return False

    def validate_tpch_schema(self) -> bool:
        # Validate that the required TPC-H dataset is loaded and available for querying.
        required_tables = [
            "customer", "lineitem", "nation", "orders", "part",
            "partsupp", "region", "supplier"
        ]

        try:
            conn = self.connect_to_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
                """
            )
            tables = {row[0] for row in cursor.fetchall()}
            conn.close()

            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                print(f"Missing tables in the TPC-H schema: {missing_tables}")
                return False

            return True
        except psycopg2.Error as e:
            raise RuntimeError(f"Error validating TPC-H schema: {e}")

    def format_qep_for_visualization(self, qep: Dict) -> Dict:
        # Format QEP data into a structured dictionary suitable for visualization.
        def traverse_plan(plan):
            formatted = {
                "Node Type": plan.get("Node Type", "Unknown"),
                "Details": {
                    "Relation Name": plan.get("Relation Name", ""),
                    "Alias": plan.get("Alias", ""),
                    "Filter": plan.get("Filter", ""),
                    "Index Cond": plan.get("Index Cond", ""),
                    "Sort Key": plan.get("Sort Key", ""),
                    "Group Key": plan.get("Group Key", ""),
                },
                "Children": []
            }

            if "Plans" in plan:
                for child in plan["Plans"]:
                    formatted["Children"].append(traverse_plan(child))

            return formatted

        return traverse_plan(qep["Plan"])

    def preprocess_qep(self, query: str) -> Dict:
        # Retrieve and preprocess the QEP for visualization.
        try:
            conn = self.connect_to_db()
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
            qep = cursor.fetchone()[0][0]
            conn.close()

            return self.format_qep_for_visualization(qep)
        except psycopg2.Error as e:
            raise RuntimeError(f"Error retrieving or formatting QEP: {e}")

    def preprocess_for_gui(self, query: str) -> Dict:
        if not self.validate_query(query):
            raise ValueError("Invalid SQL query provided.")

        qep = self.preprocess_qep(query)
        return qep

