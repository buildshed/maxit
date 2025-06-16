from agents.data_fetch_tools import get_latest_filings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os, time
from dotenv import load_dotenv
from pymongo import MongoClient
from schemas import FilingItemSummary, FilingSummary, FilingChunks, LLMGeneratedFilingItemSummary
from constants import REQUIRED_KEY_VALUES
from typing import List
from config import tickers_to_ingest, form_types_to_ingest, tenk_items_to_ingest, num_years_data_to_ingest

def generate_filing__item_structured_summary_and_chunks(
    ticker: str,
    filingdate: str,
    form: str,
    item_code: str,
    title: str,
    description: str,
    item_txt: str
) -> tuple[FilingItemSummary, List[FilingChunks]]:
    
    # 1. Structured summary via LLM
    llm = ChatOpenAI(model="gpt-4o")
    required_keys = REQUIRED_KEY_VALUES.get(item_code.upper(), [])
    required_key_text = (
        "- Try to extract the following key-value pairs if available:\n" +
        "".join(f"  • {key}\n" for key in required_keys) + "\n"
        if required_keys else ""
    )

    prompt = (
        f"You are a financial analyst assistant. Read the following text from {title} ({item_code}) "
        "of a 10-K filing. Extract and populate the following structured format:\n\n"
        f"{description}\n\n"
        "- Write a short summary (3–5 sentences).\n"
        "- Extract key numeric or categorical values as key-value pairs.\n"
        f"{required_key_text}"
        "Format your output as a LLMGeneratedFilingItemSummary(summary=..., key_values=[...]).\n\n"
        f"TEXT:\n{item_txt}"
    )

    structured_llm = llm.with_structured_output(LLMGeneratedFilingItemSummary)
    llmgen_summary = structured_llm.invoke(prompt)

    # Assemble full FilingItemSummary
    full_summary = FilingItemSummary(
        item_code=item_code,
        title=title,
        description=description,
        summary=llmgen_summary.summary,
        key_values=llmgen_summary.key_values
    )

    # 2. Chunk and embed the raw text
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    embedder = OpenAIEmbeddings(model="text-embedding-ada-002")
    chunks = splitter.split_text(item_txt)
    vectors = embedder.embed_documents(chunks)

    filing_chunks = [
        FilingChunks(
            ticker=ticker,
            filingdate=filingdate,
            form=form,
            item_code=item_code,
            chunk=chunk,
            embedding=vector
        )
        for chunk, vector in zip(chunks, vectors)
    ]

    return full_summary, filing_chunks

def main():

    start_time = time.time()
    load_dotenv()
    tickers = tickers_to_ingest
    form_type = form_types_to_ingest[0] # Just AR for now
    items_of_interest = tenk_items_to_ingest
       
    conn_string = os.getenv("MONGO_URI")

    # Connect to MongoDB
    client = MongoClient(conn_string)
    db = client["filingdb"]
    collection_filing_summary = db["all_filing_summaries"]
    collection_filing_chunks = db["all_filing_chunks"]


    # Clear old data (optional, for testing)
    collection_filing_summary.delete_many({})
    collection_filing_chunks.delete_many({})

    for ticker in tickers: 
        #get the last n ARs
        filings = get_latest_filings(ticker, form_type, n=num_years_data_to_ingest, as_text=False)
        # for each AR 
        for filing in filings:
            tenk = filing.obj()
            filing_item_summaries = []
            all_chunk_docs = []
            for item_code in items_of_interest:
                tenk_item = tenk.structure.get_item(item_code)
                title = tenk_item["Title"]
                description = tenk_item["Description"]
                item_txt = str(tenk[item_code])
                filing_item_summary, chunk_docs = generate_filing__item_structured_summary_and_chunks(ticker, filing.report_date, form_type, item_code, title, description,item_txt)
                filing_item_summaries.append(filing_item_summary)
                all_chunk_docs.extend(chunk_docs)
        
            filing_summary = FilingSummary(
                    ticker=ticker,
                    filingdate=filing.report_date,
                    form=form_type,
                    filingitemsummaries=filing_item_summaries
            )
        # Save to MongoDB
            collection_filing_summary.insert_one(filing_summary.model_dump())
            collection_filing_chunks.insert_many([chunk.model_dump() for chunk in all_chunk_docs])


    end_time = time.time()
    elapsed_seconds = end_time - start_time
    print(f"\n✅ Script completed in {elapsed_seconds:.2f} seconds.")

if __name__ == "__main__":
    main()