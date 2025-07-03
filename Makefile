# Makefile

create-app-image: 
	cd agents && langgraph build -t maxit-image 
start-services: 
	docker compose up -d
stop-services: 
	docker compose down 

# Pre-work for V2
#create-ar-memory:
#	PYTHONPATH=. python ar_pipeline/ingest_ar_filings.py && \
#	PYTHONPATH=. python ar_pipeline/create_ar_index.py
#test-ar-index: 
#	python notebooks/mongo_test.py
