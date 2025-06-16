from edgar.company_reports import TenK

REQUIRED_KEY_VALUES = {
    "ITEM 1": [
        "Number of Employees",
        "Countries of Operation",
        "Main Products",
        "Revenue Segments"
    ], 
    "ITEM 1A": [
        "FX Hedging Notional",
        "Geopolitical Risk",
        "Interest Rate Risk",
        "Supply Chain Risk"
    ],
    "ITEM 7A": [
        "FX Hedging Notional",
        "Interest Rate Swap Notional",
        "Commodity Exposure",
        "Sensitivity to Rate Movements", 
        "Key Exposure Currencies"
    ]
    }

def get_tenk_items():
    all_items = []
    #print(dir(TenK.structure))  
    all_items = []
    for part_dict in TenK.structure.structure.values():
        all_items.extend(part_dict.keys())
    return all_items

def get_tenk_item_descriptions() -> dict[str, str]:
    descriptions = {}
    for part_dict in TenK.structure.structure.values():
        for item_code, meta in part_dict.items():
            title = meta.get("Title", "")
            desc = meta.get("Description", "")
            descriptions[item_code] = f"{title}: {desc}"
    return descriptions
