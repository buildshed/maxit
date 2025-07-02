# Maxit v1 

## Installation Instructions

### Git clone the repo 
```
git clone https://github.com/2gauravc/langgraph-test.git
cd langgraph-test
```

### Create and activate an environment 
```
python3 -m venv buildshed-env
source buildshed-env/bin/activate
```

### Install dependencies 

```
pip install -r requirements.txt
```

### Edit the env file 
```
cp .env.example .env
```
Edit the .env file to provide your credentials. 

### Create the langgraph service image 
```
make create-app-image
```

### Start services 
```
make start-services
```

Confirm services are running 
```
docker ps
```

## Use the Maxit Chatbot 

### Start the Chatbot  

We use Agent vercel Chabtot to connect to our Langgraph Agent end point. 

1. Navigate to [Agent Vercel Chatbot](https://agentchat.vercel.app/) 
2. Complete the set-up 
    - Deployment URL: Provide the URL of the langgraph-api endpoint (port 8123) 
    - Assistant / Graph ID: 'agent' 
    - Langsmith API key 

Happy chatting ! 

## Inspect and Debug 

1. Connect to MongoDB 
    - Connection string: mongodb://maxit:maxit@localhost:27017/?directConnection=true
    - Connect using a mongo client such as 'MongoDB for VS Code Extension' MongoDB Compass 
2. Connect to langsmith tracing 
    - Go to https://smith.langchain.com/


## Maxit v2 (Coming soon) 

1. Ambient Agent: An Annual report Pipeline agent that runs on demand to:
     - Pull annual reports 
     - Extract key nuggets (facts) and save to memory (MongoDB)
     - Chunk and vectorize the text to store in a Vector DB (MongoDB)
2. Agentic RAG: Use AI Agent to query the RAG (as needed) 
3. Memory: Update client intelligence nuggets in memory based on user interaction (MongoDB)
4. Memory: Save analysis results to memory (pointers to results) 