from pymongo.mongo_client import MongoClient
from pymongo.operations import SearchIndexModel
import time
import os
from dotenv import load_dotenv
from config import num_embeddings_dimensions

load_dotenv()

# Connect to your Atlas deployment
uri = os.getenv("MONGO_URI")
client = MongoClient(uri)

# Access your database and collection
database = client["filingdb"]
collection = database["all_filing_chunks"]

try:
    collection.drop_search_index("vector_index")
    print("Dropped existing index 'vector_index'")
except Exception as e:
    print(f"Warning: Could not drop index. Maybe it doesn't exist yet. Details: {e}")


# Create your index model, then create the search index
search_index_model = SearchIndexModel(
  definition={
    "fields": [
      {
        "type": "vector",
        "path": "embedding",
        "numDimensions": num_embeddings_dimensions,
        "similarity": "dotProduct",
        "quantization": "scalar"
      },
      {
        "type": "filter",
        "path": "item_code"
      },
      {
        "type": "filter",
        "path": "filingdate"
      },
      {
        "type": "filter",
        "path": "ticker"
      },
    ]
  },
  name="vector_index",
  type="vectorSearch"
)

result = collection.create_search_index(model=search_index_model)
print("New search index named " + result + " is building.")

# Wait for initial sync to complete
print("Polling to check if the index is ready. This may take up to a minute.")
predicate=None
if predicate is None:
  predicate = lambda index: index.get("queryable") is True

while True:
  indices = list(collection.list_search_indexes(result))
  if len(indices) and predicate(indices[0]):
    break
  time.sleep(5)
print(result + " is ready for querying.")

client.close()
