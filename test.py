from whatif import WhatIfAnalysis

def test_retrieve_qep():
    """
    Test retrieving a QEP for a sample SQL query.
    """
    print("Initializing What-If Analysis...")
    whatif = WhatIfAnalysis()

    # Define a sample SQL query
    sample_query = """
    SELECT o_orderpriority, COUNT(*) 
    FROM orders 
    WHERE o_orderdate BETWEEN '1995-01-01' AND '1996-01-01'
    GROUP BY o_orderpriority;
    """

    print(f"Executing query: {sample_query}")
    try:
        # Retrieve the QEP
        qep = whatif.retrieve_qep(sample_query)
        print("Retrieved QEP:")
        print_qep(qep)
    except Exception as e:
        print(f"Error retrieving QEP: {e}")

def print_qep(qep):
    """
    Pretty-print the QEP in a readable format.
    :param qep: QEP dictionary.
    """
    def traverse_plan(plan, depth=0):
        indent = "  " * depth
        print(f"{indent}Node Type: {plan.get('Node Type', 'Unknown')}")
        for key in ["Relation Name", "Alias", "Filter", "Index Cond", "Sort Key", "Group Key", "Total Cost"]:
            if key in plan:
                print(f"{indent}  {key}: {plan[key]}")

        # Recursively print child nodes
        if "Plans" in plan:
            for child in plan["Plans"]:
                traverse_plan(child, depth + 1)

    print("Query Execution Plan:")
    traverse_plan(qep["Plan"])

if __name__ == "__main__":
    test_retrieve_qep()
