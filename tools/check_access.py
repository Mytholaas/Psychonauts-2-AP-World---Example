import csv
import os

# Script must be run from the repository root or the path adjusted accordingly
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print("Checking mental world access items...")
print("="*70)

csv_path = os.path.join(REPO_ROOT, "worlds", "psychonauts2", "data", "Psychonauts_2_Item_List.csv")
with open(csv_path, "r", encoding="utf-8") as f:
    items = list(csv.DictReader(f))

access_items = [i for i in items if "_Access" in i["Item"]]
print(f"\nFound {len(access_items)} access items\n")

mental_world_access = [
    "Loboto_Access", "HC_Access", "HH_Access", "Compton_Access",
    "PsiKing_Access", "Ford_Access", "StrikeCity_Access", "Cruller_Access",
    "Tomb_Access", "Bob_Access", "Cassie_Access", "Lucy_Access", "Nick_Access"
]

issues = []
for item in access_items:
    if item["Item"] in mental_world_access:
        req = item.get("Item_Required", "NULL")
        status = "OK" if req == "NULL" or not req else "!!"
        print(f"{status} {item['Item']:20} | Requires: {req}")
        if "MentalConnection" in req or "Mental" in req:
            issues.append((item["Item"], req))

print("\n" + "="*70)
if not issues:
    print("SUCCESS: No mental world access items require Mental Connection")
    print("Collective Unconscious navigation will work correctly")
else:
    print(f"FOUND {len(issues)} ISSUES!")
    for item_name, req in issues:
        print(f"  - {item_name} requires: {req}")
