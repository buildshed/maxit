from pymongo import MongoClient

# Connect to MongoDB (update the URI as needed)
client = MongoClient("mongodb://maxit:maxit@localhost:27017/?directConnection=true") 
db = client["filingdb"]  
collection = db["all_filing_chunks"]  

pipeline = [
    {"$match": {"ticker": "MU", "form": "10-K"}},
    {"$group": {"_id": "$filingdate", "count": {"$sum": 1}}},
    {"$sort": {"_id": 1}}  # sort by date
]

results = collection.aggregate(pipeline)

# Print the results
print("Document count per filing date for MU 10-K:")
for result in results:
    print(f"{result['_id']}: {result['count']}")
