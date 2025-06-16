import os, pymongo
from openai import OpenAI
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from utils import infer_relevant_items
from constants import get_tenk_item_descriptions
from config import numCandidates, limit

def main():
  load_dotenv()
  uri = os.getenv("MONGO_URI")

  # connect to your Atlas cluster
  client_mongo = pymongo.MongoClient(uri)

  query_text = "What interest rate risks does Micron face?"

  # Create the query embeddings 
  client_openai = OpenAI()
  response = client_openai.embeddings.create(
      input=query_text,
      model="text-embedding-ada-002"
  )
  embedding = response.data[0].embedding

  # Find relevant item(s) from the tenk that should be used 
  item_map = get_tenk_item_descriptions()
  relevant_items = infer_relevant_items(query_text, item_map)
  print(f"🔎 Relevant 10-K item codes for query \"{query_text}\": {relevant_items}")

  # define pipeline
  pipeline = [
    {
      '$vectorSearch': {
        'index': 'vector_index', 
        'path': 'embedding', 
        'queryVector': embedding, 
        'numCandidates': numCandidates, 
        'limit': limit, 
        'filter': {
          'item_code': {'$in': relevant_items}
        }
      }
    }, {
      '$project': {
        '_id': 0, 
        'ticker': 1, 
        'filingdate': 1,
        'item_code': 1,
        'chunk': 1,
        'score': {
          '$meta': 'vectorSearchScore'
        }
      }
    }
  ]

  # run pipeline
  result_cursor = client_mongo["filingdb"]["all_filing_chunks"].aggregate(pipeline)

  # print results
  for i in result_cursor:
    print(i)

  retrieved_docs = list(result_cursor)
  retrieved_chunks = [doc["chunk"] for doc in retrieved_docs if "chunk" in doc]
  #print(retrieved_chunks)
  # Optional: Truncate or filter very long content if needed
  context = "\n\n".join(retrieved_chunks)  
  # Prepare the prompt
  final_prompt = (
    f"You are a financial analyst assistant. Based on the 10-K excerpts below, answer the question:\n\n"
    f"Question: {query_text}\n\n"
    f"Excerpts:\n{context}\n\n"
    f"Answer in a clear, concise, and professional tone suitable for an RM (Relationship Manager)."
)
  # Call the LLM to generate the final answer
  llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
  final_answer = llm.invoke(final_prompt)
  print("\n🧠 Final Answer:\n")
  print(final_answer)


if __name__ == "__main__":
    main()