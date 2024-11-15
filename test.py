from preprocessing import Preprocessing, validate_and_load_tpch, preprocess_query_for_gui

def test_tpch_schema():
    print("Testing TPC-H Schema Validation...")
    preprocessing = Preprocessing()
    if preprocessing.validate_tpch_schema():
        print("TPC-H schema validation passed.")
    else:
        print("TPC-H schema validation failed.")

def test_query_validation():
    query = "SELECT * FROM orders WHERE o_orderdate > '1995-01-01';"
    preprocessing = Preprocessing()
    print(f"Testing Query Validation for: {query}")
    if preprocessing.validate_query(query):
        print("Query validation passed.")
    else:
        print("Query validation failed.")

def test_qep_preprocessing():
    query = "SELECT * FROM orders WHERE o_orderdate > '1995-01-01';"
    preprocessing = Preprocessing()
    print(f"Testing QEP Preprocessing for: {query}")
    try:
        qep = preprocessing.preprocess_qep(query)
        print("Formatted QEP for visualization:", qep)
    except Exception as e:
        print(f"Error in QEP Preprocessing: {e}")

if __name__ == "__main__":
    test_tpch_schema()
    test_query_validation()
    test_qep_preprocessing()
