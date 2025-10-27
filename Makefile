.PHONY: help docs-dev docs-build docs-export docs-clean docs-gen docs-brand-check

# Default target
help:
	@echo "Kearney Data Platform - Makefile"
	@echo ""
	@echo "Documentation Commands:"
	@echo "  make docs-dev          Start Docusaurus dev server"
	@echo "  make docs-build        Build documentation for production"
	@echo "  make docs-gen          Generate API/CLI/design token docs"
	@echo "  make docs-brand-check  Check documentation for brand compliance"
	@echo "  make docs-export       Export documentation as PDFs"
	@echo "  make docs-clean        Clean documentation build files"
	@echo ""
	@echo "Server Commands:"
	@echo "  make server-start      Start FastAPI server"
	@echo "  make server-stop       Stop FastAPI server"
	@echo ""
	@echo "Development Commands:"
	@echo "  make install           Install Python dependencies"
	@echo "  make test              Run tests"
	@echo "  make lint              Run linters"
	@echo "  make format            Format code"

# Documentation commands
docs-dev:
	@echo "Starting Docusaurus development server..."
	cd site && npm install && npm start

docs-build: docs-gen
	@echo "Building documentation..."
	cd site && npm install && npm run build
	@echo "Build complete! Output in site/build"

docs-gen:
	@echo "Generating documentation..."
	@echo "1. Generating design token docs..."
	python3 scripts/sync_tokens_for_docs.py
	@echo "2. Generating API docs (if server is running)..."
	-python3 scripts/gen_openapi_docs.py
	@echo "3. Generating CLI docs (if CLI is installed)..."
	-python3 scripts/gen_cli_docs.py
	@echo "Documentation generation complete!"

docs-brand-check:
	@echo "Checking brand compliance..."
	python3 scripts/brand_guard_docs.py

docs-export:
	@echo "Exporting PDFs..."
	@echo "1. Building documentation..."
	cd site && npm run build
	@echo "2. Starting local server..."
	cd site && npx serve build -p 3000 &
	@sleep 5
	@echo "3. Exporting PDFs..."
	npx ts-node scripts/export_pdfs.ts
	@echo "4. Stopping server..."
	@pkill -f "serve build" || true
	@echo "PDFs exported to site/pdfs/"

docs-clean:
	@echo "Cleaning documentation build files..."
	rm -rf site/build
	rm -rf site/.docusaurus
	rm -rf site/node_modules
	rm -rf site/pdfs
	@echo "Clean complete!"

# Server commands
server-start:
	@echo "Starting FastAPI server..."
	orchestrator server start --port 8000

server-stop:
	@echo "Stopping FastAPI server..."
	orchestrator server stop

# Development commands
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements-dataplatform.txt
	pip install -e .
	@echo "Installing Node dependencies..."
	cd site && npm install
	cd apps/web && npm install

test:
	@echo "Running tests..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	@echo "Running linters..."
	ruff check src/ tests/
	mypy src/
	cd apps/web && npm run lint

format:
	@echo "Formatting code..."
	black src/ tests/ scripts/
	ruff check --fix src/ tests/
	cd apps/web && npm run format

# === Orchestrator Task Controls ==============================================
# Usage:
#   make review-task  PROJECT=white_mold_scenario_planner TASK=02_DATA_EXPORT
#   make approve-task PROJECT=white_mold_scenario_planner TASK=02_DATA_EXPORT

# Root where project repos live
PROJECTS_ROOT := /Users/pfay01/Projects

# Derived paths
PROJECT_DIR   := $(PROJECTS_ROOT)/$(PROJECT)
ART_DIR       := $(PROJECT_DIR)/TASKS/_artifacts
STATUS_DIR    := $(PROJECT_DIR)/TASKS/_status
STATUS_FILE   := $(STATUS_DIR)/$(TASK).status
RESULTS_MD    := $(ART_DIR)/$(shell echo $(TASK) | sed 's/_/-/g')_RESULTS.md

# Helper: current timestamp (portable)
NOW := $(shell date +"%Y-%m-%dT%H:%M:%S%z")

.PHONY: review-task approve-task show-task

review-task:
	@if [ -z "$(PROJECT)" ] || [ -z "$(TASK)" ]; then \
		echo "❌ Set PROJECT= and TASK= (e.g., TASK=02_DATA_EXPORT)"; exit 1; fi
	@mkdir -p "$(STATUS_DIR)"
	@echo "STATUS: READY_FOR_REVIEW" > "$(STATUS_FILE)"
	@echo "TASK: $(TASK)"           >> "$(STATUS_FILE)"
	@echo "PROJECT: $(PROJECT)"     >> "$(STATUS_FILE)"
	@echo "UPDATED: $(NOW)"         >> "$(STATUS_FILE)"
	@# Soft-annotate results MD if present (non-fatal if missing)
	@if [ -f "$(RESULTS_MD)" ]; then \
		grep -q "READY_FOR_REVIEW" "$(RESULTS_MD)" || echo "\n\nSTATUS: READY_FOR_REVIEW ($(NOW))" >> "$(RESULTS_MD)"; \
	fi
	@echo "✅ Marked $(PROJECT):$(TASK) as READY_FOR_REVIEW"
	@echo " → $(STATUS_FILE)"

approve-task:
	@if [ -z "$(PROJECT)" ] || [ -z "$(TASK)" ]; then \
		echo "❌ Set PROJECT= and TASK= (e.g., TASK=02_DATA_EXPORT)"; exit 1; fi
	@mkdir -p "$(STATUS_DIR)"
	@echo "STATUS: APPROVED"        >  "$(STATUS_FILE)"
	@echo "TASK: $(TASK)"           >> "$(STATUS_FILE)"
	@echo "PROJECT: $(PROJECT)"     >> "$(STATUS_FILE)"
	@echo "UPDATED: $(NOW)"         >> "$(STATUS_FILE)"
	@# Add approval token to results MD if present
	@if [ -f "$(RESULTS_MD)" ]; then \
		grep -q "APPROVED" "$(RESULTS_MD)" || echo "\n\n✅ $(TASK) APPROVED ($(NOW))" >> "$(RESULTS_MD)"; \
	fi
	@echo "🔒 Approved $(PROJECT):$(TASK)"
	@echo " → $(STATUS_FILE)"

show-task:
	@if [ -z "$(PROJECT)" ] || [ -z "$(TASK)" ]; then \
		echo "❌ Set PROJECT= and TASK="; exit 1; fi
	@cat "$(STATUS_FILE)" 2>/dev/null || echo "No status file at $(STATUS_FILE)"
