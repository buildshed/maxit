from pymongo import MongoClient

# Connect to MongoDB (update the URI as needed)
client = MongoClient("mongodb://maxit:maxit@localhost:27017/?directConnection=true") 
db = client["filingdb"]  
stats = db.command("dbstats", scale=1024 * 1024)  # in MB

print(f"Database size: {stats['dataSize']} MB")
print(f"Storage size: {stats['storageSize']} MB")