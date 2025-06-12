docker run -d \
  --name local_dev_atlas \
  -p 27017:27017 \
  -e MONGODB_INITDB_ROOT_USERNAME=maxit \
  -e MONGODB_INITDB_ROOT_PASSWORD=maxit \
  -v maxit-db:/data/db \
  mongodb/mongodb-atlas-local:8.0 \
  mongod --bind_ip_all


Mongo CLI Setup to run vector search 

1. Install Mongo and associated tools 
Install brew: 
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
- Follow the instructions to set up env stuff for brew 

Set-up Atlas CLI 
brew install mongodb-atlas-cli
atlas setup - to link acount with CLI 

Install Atlas (mongo) 
atlas deployments setup

Note the connection string: 
mongodb://localhost:32768/?directConnection=true

2. Push data 

cd langgraph-app
make run-ar

3. Create Index 
python ar_pipeline/create_index.py 

4. Query Index 