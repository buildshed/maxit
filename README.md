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

pip install -r requirements.txt


### Edit the env file 
```
cp .env.example .env
```
Edit the .env file to provide your credentials. 

### Create the langgraph service image 

```
cd agents/
langgraph build -t maxit-image
```

### Start services 

```
cd ..
docker compose up -d
```

Confirm services are running 

```
docker ps
```

### Create Long term Memory  

2. Push data 

cd langgraph-app
make run-ar

3. Create Index 
python ar_pipeline/create_index.py 


### Start chatting 

navigate to 

[Chat Endpoint](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123)

If you are running services on a hosted platform (such as AWS EC2 or Github codespaces)

[Chat Endpoint](https://smith.langchain.com/studio/?baseUrl=your_public_deployed_endpoint)
