import subprocess
import time

# Function to test the QEP interface generation
def test_qep_interface():
    # Here, we'll simulate launching the GUI
    try:
        # Launch the GUI
        subprocess.run(["python", "interface.py"], check=True)

        # Allow the GUI to load
        time.sleep(2)

        # Simulate entering a SQL query
        print("Test: Simulating SQL query input...")
        sql_query = "SELECT * FROM customer C, orders O WHERE C.c_custkey = O.o_custkey"
        
        # You can manually input the query in the GUI, or add extra logic to simulate user input
        
        # Test visualizing the QEP for the input query
        print("Test: Visualizing QEP...")
        # After clicking 'Visualize QEP', the Pyvis visualization should be generated
        
        # Test modifying the QEP (e.g., changing the node type to Hash Join)
        modification = {"Node Type": "Hash Join"}
        print(f"Test: Modifying QEP with modification: {modification}")
        # This simulates modifying the QEP by changing its join type (this can be handled in the GUI interactively)
        
        # Wait for the user interaction or for the modifications to be applied
        time.sleep(3)

        print("Test: Successfully ran the QEP Interface")
    
    except Exception as e:
        print(f"Test failed with error: {e}")

# Run the test
if __name__ == "__main__":
    test_qep_interface()
