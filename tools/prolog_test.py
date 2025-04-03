# Import the Prolog interface from pyswip
from pyswip import Prolog, Functor, Variable, Atom # Removed prolog_to_python
import os # Used to check if the file exists
import sys # Used for stderr

# --- Configuration ---
KB_FILENAME = 'ssense_policy.pl'

def format_result(solutions):
    """Formats Prolog query results for printing."""
    if not solutions:
        return "No solution found."
    if solutions == [{}]: # Query succeeded with no variables
        return "True"

    formatted = []
    for sol in solutions:
        if not sol: # Handle cases like 'true' that might yield {}
             continue
        parts = []
        for var_name, value in sol.items():
            # Rely on pyswip's default conversion and repr() for display
            # This will handle basic types and show structure of compound terms
            parts.append(f"{var_name} = {value!r}") # Use repr for clarity
        formatted.append(", ".join(parts))
    # Handle case where query succeeds but binds no variables explicitly in the result dict
    return "\n - ".join(formatted) if formatted else "True (no variables bound)"


def run_query(prolog, query_str, expected_outcome_desc):
    """Runs a single query and prints results."""
    print(f"\nQuery: {query_str}")
    print(f"Expected: {expected_outcome_desc}")
    try:
        solutions = list(prolog.query(query_str))
        print(f"Result:\n - {format_result(solutions)}")
        return solutions # Return solutions for potential further checks
    except Exception as e:
        print(f"Error running query: {e}", file=sys.stderr)
        return None

def run_prolog_tests():
    """
    Loads the SSENSE return policy knowledge base and runs a comprehensive test suite.
    """
    prolog = Prolog()

    # --- 1. Load the Knowledge Base ---
    if not os.path.exists(KB_FILENAME):
        print(f"Error: Knowledge base file '{KB_FILENAME}' not found.", file=sys.stderr)
        print(f"Please save the updated Prolog code to '{KB_FILENAME}' or update the path.", file=sys.stderr)
        return

    try:
        print(f"Consulting '{KB_FILENAME}'...")
        # Use consult - it's generally preferred for loading .pl files
        prolog.consult(KB_FILENAME)
        print("Knowledge base loaded successfully.")
    except Exception as e:
        print(f"Error loading knowledge base: {e}", file=sys.stderr)
        print("Check Prolog file syntax, file path, and SWI-Prolog installation.", file=sys.stderr)
        return

    print("\n" + "="*10 + " Running Basic Fact Queries " + "="*10)
    # --- 2. Basic Fact Queries ---
    run_query(prolog, "has_attribute(p1, strict_no_paper_policy, true).", "True")
    run_query(prolog, "has_attribute(req, request_window_unit, calendar_days).", "True")
    run_query(prolog, "excluded_fee(excl, shipping_fees).", "True")

    print("\n" + "="*10 + " Running Queries with Variable Binding " + "="*10)
    # --- 3. Queries with Variable Binding ---
    run_query(prolog, "has_attribute(p1, policy_name, Name).", f"Name = {'SSENSE Return Policy'!r}") # Use repr for expected string
    run_query(prolog, "requires(crit, item_condition, Cond).", f"Cond = {'original'!r}")
    run_query(prolog, "shipping_cost(ship, region(uk), Cost).", f"Cost = {'fee_deducted'!r}")
    # Expected output for compound terms might look like Term(b'amount', [60, b'aud']) depending on pyswip version
    run_query(prolog, "return_fee(ship, region(australia), Fee).", "Fee = amount(60, aud) structure (check output)")

    print("\n" + "="*10 + " Running Queries with Multiple Solutions " + "="*10)
    # --- 4. Queries with Multiple Solutions ---
    run_query(prolog, "excluded_item_type(excl, ItemType, reason(hygiene)).", f"ItemType = {'face_mask'!r}\n - ItemType = {'face_covering'!r}")
    run_query(prolog, "initiation_method(req, guest, Method).", f"Method = {'create_account_same_email'!r}\n - Method = {'use_self_service_tool'!r}\n - Method = {'contact_customer_care'!r}")


    print("\n" + "="*10 + " Running Core Logic Queries (is_eligible/5) " + "="*10)
    # --- 5. Test the is_eligible/5 Core Logic ---
    run_query(prolog, "is_eligible(shoes, original, original_intact, intact, 15).", "True (Eligible standard item)")
    run_query(prolog, "is_eligible(shoes, original, original_intact, intact, 30).", "True (Eligible standard item, edge of window)")
    run_query(prolog, "is_eligible(shoes, original, original_intact, intact, 31).", "False (Outside return window)")
    run_query(prolog, "is_eligible(final_sale_item, original, original_intact, intact, 10).", "False (Excluded item type)")
    run_query(prolog, "is_eligible(face_mask, original, original_intact, intact, 10).", "False (Excluded item type)")
    run_query(prolog, "is_eligible(sweater, used, original_intact, intact, 15).", "False (Wrong condition)")
    run_query(prolog, "is_eligible(sweater, original, opened_box, intact, 15).", "False (Wrong packaging)")
    run_query(prolog, "is_eligible(sweater, original, original_intact, removed, 15).", "False (Wrong tag status)")
    run_query(prolog, "is_eligible(self_care, original, sealed, intact, 10).", "True (Eligible sealed item)")
    run_query(prolog, "is_eligible(self_care, original, original_intact, intact, 10).", "False (Sealed item not sealed)")
    run_query(prolog, "is_eligible(swimwear, original, original_intact, hygienic_sticker_intact, 10).", "True (Eligible swimwear with sticker)")
    run_query(prolog, "is_eligible(swimwear, original, original_intact, intact, 10).", "False (Swimwear requires hygienic sticker)")
    run_query(prolog, "is_eligible(technology, original, original_intact, intact, 10).", "True (Eligible technology - placeholder rule)")
    # Assuming dangerous_good is correctly listed in excluded_item_type now
    run_query(prolog, "is_eligible(dangerous_good, original, original_intact, intact, 10).", "False (Excluded 'dangerous_good')")


    print("\n" + "="*10 + " Running LLM Helper Predicate Queries " + "="*10)
    # --- 6. Test the LLM Helper Predicates ---

    # get_return_window/1
    run_query(prolog, "get_return_window(Days).", "Days = 30")

    # get_shipping_cost/2
    run_query(prolog, "get_shipping_cost(canada, Cost).", f"Cost = {'free'!r}")
    run_query(prolog, "get_shipping_cost(uk, Cost).", f"Cost = {'fee_deducted'!r}")
    run_query(prolog, "get_shipping_cost(other_international, Cost).", f"Cost = {'customer_pays'!r}")
    run_query(prolog, "get_shipping_cost(france, Cost).", "No solution found")

    # get_return_label_info/2
    run_query(prolog, "get_return_label_info(usa, Info).", f"Info = {'ppl_via_email'!r}")
    run_query(prolog, "get_return_label_info(other_international, Info).", f"Info = {'ra_number_via_email'!r}")

    # get_return_fee/3
    run_query(prolog, "get_return_fee(uk, Amount, Currency).", f"Amount = 34, Currency = {'gbp'!r}")
    run_query(prolog, "get_return_fee(australia, Amount, Currency).", f"Amount = 60, Currency = {'aud'!r}")
    run_query(prolog, "get_return_fee(canada, Amount, Currency).", "No solution found")
    run_query(prolog, "get_return_fee(usa, Amount, Currency).", "No solution found")

    # is_item_excluded/2
    run_query(prolog, "is_item_excluded(final_sale_item, Reason).", f"Reason = {'marked_final_sale'!r}")
    run_query(prolog, "is_item_excluded(face_mask, Reason).", f"Reason = {'hygiene'!r}")
    run_query(prolog, "is_item_excluded(sexual_wellness_toy, Reason).", f"Reason = {'health_and_safety'!r}")
    run_query(prolog, "is_item_excluded(shoes, Reason).", "No solution found")
    # Checking the list structure - repr might show bytes (b'...') depending on version/encoding
    run_query(prolog, "is_item_excluded(dangerous_good, Reason).", "Reason = includes([...]) structure (check output)")

    # get_initiation_method/2
    run_query(prolog, "get_initiation_method(account_holder, Method).", f"Method = {'via_order_history'!r}")
    run_query(prolog, "get_initiation_method(guest, Method).", f"Method = {'create_account_same_email'!r}\n - Method = {'use_self_service_tool'!r}\n - Method = {'contact_customer_care'!r}")
    run_query(prolog, "get_initiation_method(general, Method).", f"Method = {'contact_customer_care'!r}")

    # can_exchange/1
    run_query(prolog, "can_exchange(Result).", "Result = False")

    # get_contact_email/1
    run_query(prolog, "get_contact_email(Email).", f"Email = {'customercare@ssense.com'!r}")

    # get_contact_chat_availability/1
    run_query(prolog, "get_contact_chat_availability(Avail).", f"Avail = {'24/7'!r}")

    # get_phone_number/3
    run_query(prolog, "get_phone_number(north_america_toll_free, Num, Hours).", f"Num = '1-877-637-6002', Hours = {'Mon-Fri 9AM-8PM EST, Sat 9AM-5PM EST'!r}")
    run_query(prolog, "get_phone_number(local, Num, Hours).", f"Num = '1-514-600-5818', Hours = {'Mon-Fri 9AM-8PM EST, Sat 9AM-5PM EST'!r}")
    run_query(prolog, "get_phone_number(quebec, Num, Hours).", f"Num = '1-514-700-2078', Hours = {'Mon-Fri 9AM-8PM EST, Sat 9AM-5PM EST'!r}")
    run_query(prolog, "get_phone_number(uk_number, Num, Hours).", "No solution found")

    # get_damaged_item_action/1
    run_query(prolog, "get_damaged_item_action(Action).", f"Action = {'contact_customer_care'!r}")

    # get_warranty_provider/1
    run_query(prolog, "get_warranty_provider(Provider).", f"Provider = {'manufacturer'!r}")

    # is_warranty_by_ssense/1
    run_query(prolog, "is_warranty_by_ssense(Result).", "Result = False")


    print("\n" + "="*10 + " Testing Complete " + "="*10)

# Run the test function
if __name__ == "__main__":
    print("Starting SSENSE Return Policy KB Test Suite...")
    print(f"Attempting to load KB from: '{os.path.abspath(KB_FILENAME)}'")
    run_prolog_tests()
    print("Test Suite Finished.")