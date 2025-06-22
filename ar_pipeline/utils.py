from edgar.company_reports import TenK
from schemas import InferredItemCodes
from typing_extensions import List

def validate_item_codes(codes: List[str], allowed: List[str]) -> List[str]:
    valid = [code for code in codes if code in allowed]
    invalid = [code for code in codes if code not in allowed]

    if invalid:
        print(f"⚠️ Warning: Ignoring invalid item codes: {invalid}")

    return valid
