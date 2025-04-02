# Import the Prolog interface from pyswip
# Removed PrologError from the import statement as it might not be available
# in all versions directly from the top-level package.
from pyswip import Prolog
import os # Used to check if the file exists

def run_prolog_tests():
    """
    Loads the return_policy.pl knowledge base and runs test queries using pyswip.
    Handles potential errors during knowledge base loading.
    """
    prolog = Prolog()
    kb_file = 'ssense_policy.pl' # Make sure this file exists

    # --- 1. Load the Knowledge Base ---
    if not os.path.exists(kb_file):
        print(f"Error: Knowledge base file '{kb_file}' not found.")
        print("Please ensure the file is in the same directory as this script.")
        return

    try:
        print(f"Consulting '{kb_file}'...")
        # The consult method itself might raise an exception on failure
        prolog.consult(kb_file)
        print("Knowledge base loaded successfully.")
    # Catching a more general Exception as PrologError might not be importable
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        print("This might indicate an issue with the Prolog file syntax or SWI-Prolog setup.")
        return

    print("\n--- Running Test Queries ---")

    # --- 2. Run Queries ---

    # Example 1: Check a specific fact (Boolean result)
    query1 = "has_attribute(p1, strict_no_paper_policy, true)."
    print(f"\nQuery: {query1}")
    try:
        result1 = list(prolog.query(query1))
        print(f"Result: {'True' if result1 else 'False'}")
    except Exception as e:
        print(f"Error running query: {e}")


    # Example 2: Find an attribute value (Single variable binding)
    query2 = "has_attribute(req, request_window_duration, Duration)."
    print(f"\nQuery: {query2}")
    try:
        result2 = list(prolog.query(query2))
        if result2:
            print(f"Result: Duration = {result2[0]['Duration']}")
        else:
            print("Result: No solution found.")
    except Exception as e:
        print(f"Error running query: {e}")


    # Example 3: Query with compound terms (Single variable binding)
    query3 = "shipping_cost(ship, region(canada), Cost)."
    print(f"\nQuery: {query3}")
    try:
        result3 = list(prolog.query(query3))
        if result3:
            print(f"Result: Cost = {result3[0]['Cost']}")
        else:
            print("Result: No solution found.")
    except Exception as e:
        print(f"Error running query: {e}")


    # Example 4: Query with compound terms (Value is a compound term)
    query4 = "return_fee(ship, region(australia), Fee)."
    print(f"\nQuery: {query4}")
    try:
        result4 = list(prolog.query(query4))
        if result4:
            fee_term = result4[0]['Fee']
            # Attempt to format compound term nicely, fallback to raw output
            try:
                if hasattr(fee_term, 'name') and hasattr(fee_term, 'args'):
                     print(f"Result: Fee = {fee_term.name}{tuple(fee_term.args)}")
                else:
                     print(f"Result: Fee = {fee_term}")
            except Exception:
                 print(f"Result: Fee = {fee_term}")
        else:
            print("Result: No solution found.")
    except Exception as e:
        print(f"Error running query: {e}")


    # Example 5: Find multiple answers (Iterate through results)
    query5 = "excluded_item_type(excl, ItemType, reason(hygiene))."
    print(f"\nQuery: {query5}")
    print("Results:")
    try:
        solutions5 = list(prolog.query(query5))
        if solutions5:
            for solution in solutions5:
                print(f" - ItemType = {solution['ItemType']}")
        else:
            print(" - No solution found.")
    except Exception as e:
        print(f"Error running query: {e}")


    # Example 6: Check a boolean attribute
    query6 = "has_attribute(exch, direct_exchange_offered, false)."
    print(f"\nQuery: {query6}")
    try:
        result6 = list(prolog.query(query6))
        print(f"Result: {'True' if result6 else 'False'}")
    except Exception as e:
        print(f"Error running query: {e}")


    # Example 7: Find required actions
    query7 = "required_action(dmg, customer, Action)."
    print(f"\nQuery: {query7}")
    try:
        result7 = list(prolog.query(query7))
        if result7:
            print(f"Result: Action = {result7[0]['Action']}")
        else:
            print("Result: No solution found.")
    except Exception as e:
        print(f"Error running query: {e}")


    # Example 8: List all defined entities (Iterate through results)
    query8 = "entity(EntityType)."
    print(f"\nQuery: {query8}")
    print("Results:")
    try:
        solutions8 = list(prolog.query(query8))
        if solutions8:
            for solution in solutions8:
                 print(f" - EntityType = {solution['EntityType']}")
        else:
             print(" - No solution found.")
    except Exception as e:
        print(f"Error running query: {e}")


    print("\n--- Testing Complete ---")

# Run the test function
if __name__ == "__main__":
    run_prolog_tests()
