# Makefile

# Target to run the annual report pipeline
run-ar:
	PYTHONPATH=. python ar_pipeline/ar_pipeline.py
