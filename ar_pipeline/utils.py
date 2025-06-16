from edgar.company_reports import TenK
from langchain_openai import ChatOpenAI
from schemas import InferredItemCodes
from typing_extensions import List

def infer_relevant_items(query: str, item_map: dict[str, str]) -> list[str]:
    item_list_str = "\n".join([f"{code}: {desc}" for code, desc in item_map.items()])
    prompt = (
        f"You are a smart assistant that maps user questions to relevant items from a 10-K filing.\n\n"
        f"Question: \"{query}\"\n\n"
        f"Choose one or more relevant items from the list below based on the topic of the question.\n"
        f"Format your output as InferredItemCodes(item_codes=[...])\n\n"
        f"Available Items:\n{item_list_str}"
    )
    llm = ChatOpenAI(model="gpt-4o")
    structured_llm =llm.with_structured_output(InferredItemCodes)
    response = structured_llm.invoke(prompt)
    return response.item_codes

def validate_item_codes(codes: List[str], allowed: List[str]) -> List[str]:
    valid = [code for code in codes if code in allowed]
    invalid = [code for code in codes if code not in allowed]

    if invalid:
        print(f"⚠️ Warning: Ignoring invalid item codes: {invalid}")

    return valid
