.PHONY: setup download analyze kg app full test clean help

help:
	@echo "CD46 Precision Medicine Platform — Available Commands:"
	@echo "  make setup      Install all Python dependencies"
	@echo "  make download   Download all datasets (TCGA ~4min + APIs ~2min)"
	@echo "  make analyze    Run all analysis scripts"
	@echo "  make kg         Build Neo4j knowledge graph (AuraDB)"
	@echo "  make app        Launch Streamlit app locally"
	@echo "  make full       End-to-end: download + analyze + kg + app"
	@echo "  make test       Run test suite with coverage"
	@echo "  make clean      Remove all downloaded + processed data"

setup:
	pip install -r requirements.txt

download:
	python scripts/run_pipeline.py --mode download

analyze:
	python scripts/run_pipeline.py --mode analyze

kg:
	python scripts/run_pipeline.py --mode kg

app:
	streamlit run app/streamlit_app.py

agent:
	python scripts/run_pipeline.py --mode agent

full:
	python scripts/run_pipeline.py --mode full

report:
	python scripts/run_pipeline.py --mode report

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

clean:
	rm -rf data/raw data/processed reports/figures
	@echo "Cleaned raw + processed data. AuraDB not affected."

clean-processed:
	rm -rf data/processed reports/figures

lint:
	python -m py_compile src/**/*.py app/**/*.py scripts/*.py
	@echo "Syntax check passed"
