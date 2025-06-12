import pymongo
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

# connect to your Atlas cluster
client_mongo = pymongo.MongoClient("mongodb://maxit:maxit@localhost:27017/?directConnection=true")

query_text = "What currency risks does Micron face?"
client_openai = OpenAI()
response = client_openai.embeddings.create(
    input=query_text,
    model="text-embedding-ada-002"
)
embedding = response.data[0].embedding
# define pipeline
pipeline = [
  {
    '$vectorSearch': {
      'index': 'vector_index', 
      'path': 'embedding', 
      'queryVector': embedding, 
      'numCandidates': 150, 
      'limit': 10
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
result = client_mongo["filingdb"]["all_filing_chunks"].aggregate(pipeline)

# print results
for i in result:
    print(i)
 