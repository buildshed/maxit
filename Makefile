# Makefile

# Target to run the annual report pipeline
run-ar-pipeline:
	PYTHONPATH=. python ar_pipeline/ar_pipeline.py && \
	PYTHONPATH=. python ar_pipeline/create_index.py