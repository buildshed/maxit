# Makefile
.PHONY: run-ar-pipeline query-ar-memory

create-app-image: 
	cd agents && langgraph build -t maxit-image --no-cache
start-services: 
	docker compose up -d
create-ar-memory:
	PYTHONPATH=. python ar_pipeline/ingest_ar_filings.py && \
	PYTHONPATH=. python ar_pipeline/create_ar_index.py
test-ar-index: 
	python notebooks/mongo_test.py
