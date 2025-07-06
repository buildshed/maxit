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
The following services are started: 

1. langgraph-api-1 on port 8123: This is the api back end 
2. frontend-1 on port 3000: This is the chat UI
3. A postgres and a redis service that is used internally by the api back end 

## Use the Maxit Chatbot 

### Start the Chatbot  

1. Navigate to the Chat UI at http://localhost:3000 
2. Complete the set-up 
    - Deployment URL: http://localhost:8123 (api back end)   
    - Assistant / Graph ID: 'agent' 
    - Langsmith API key

Happy chatting ! 

Note: Installing on a cloud server (Like Digital Ocean or AWS) or on a cloud absed IDE like Github Codespaces? Refer [INSTALL EXTRAS](./install_extras.md)


## Maxit v2 (Coming soon) 

1. Ambient Agent: An Annual report Pipeline agent that runs on demand to:
     - Pull annual reports 
     - Extract key nuggets (facts) and save to memory (MongoDB)
     - Chunk and vectorize the text to store in a Vector DB (MongoDB)
2. Agentic RAG: Use AI Agent to query the RAG (as needed) 
3. Memory: Update client intelligence nuggets in memory based on user interaction (MongoDB)
4. Memory: Save analysis results to memory (pointers to results) 