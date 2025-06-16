# Makefile
.PHONY: run-ar-pipeline query-ar-memory

# Target to run the annual report pipeline
create-ar-memory:
	PYTHONPATH=. python ar_pipeline/ingest_ar_filings.py && \
	PYTHONPATH=. python ar_pipeline/create_ar_index.py
# target to query the pipeline 
query-ar-memory: 
	PYTHONPATH=. python ar_pipeline/query_ar_index.py