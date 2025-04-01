from pyswip import Prolog

prolog = Prolog()
prolog.consult("ssense_policy_rules_safe_final.pl")

print("Final Sale Items:")
for result in prolog.query("final_sale(Item, Category)."):
    print(result)

print("\nFinal Sale Items with Reasons:")
for result in prolog.query("final_sale(Item, Category), final_sale_reason(Item, Reason)."):
    print(result)
