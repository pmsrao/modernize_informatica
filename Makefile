.PHONY: help upload parse enhance hierarchy lineage canonical code review diff clean clean-all test-all

# Configuration
API_URL ?= http://localhost:8000
TEST_LOG_DIR = test_log
STAGING_DIR = $(TEST_LOG_DIR)/staging
PARSED_DIR = $(TEST_LOG_DIR)/parsed
PARSE_AI_DIR = $(TEST_LOG_DIR)/parse_ai
GENERATED_DIR = $(TEST_LOG_DIR)/generated
GENERATED_AI_DIR = $(TEST_LOG_DIR)/generated_ai

# Default target
help:
	@echo "Informatica Modernization - Step-by-Step Testing"
	@echo ""
	@echo "Available targets:"
	@echo "  make upload FILES='path/to/file1.xml path/to/file2.xml'  - Upload files to staging"
	@echo "  make parse                                              - Parse all mappings"
	@echo "  make enhance                                            - Enhance parsed models with AI"
	@echo "  make hierarchy                                          - Generate hierarchy/tree structure"
	@echo "  make lineage                                            - Generate lineage diagrams"
	@echo "  make canonical                                          - Generate canonical model images"
	@echo "  make code                                               - Generate code (PySpark/DLT/SQL)"
	@echo "  make review                                             - Review & fix code with AI"
	@echo "  make diff                                               - Generate diff reports (parse vs enhance, code vs review)"
	@echo "  make test-all                                           - Run all steps in sequence (logs to exec_steps_logs.txt)"
	@echo "  make clean                                              - Clean test_log directory contents (keeps structure)"
	@echo "  make clean-all                                          - Remove test_log directory completely"
	@echo ""
	@echo "Example:"
	@echo "  make upload                                    # Uses default: samples/super_complex/*.xml"
	@echo "  make upload FILES='samples/complex/*.xml'      # Use custom files"
	@echo "  make parse"

# Create directory structure
$(TEST_LOG_DIR):
	mkdir -p $(STAGING_DIR) $(PARSED_DIR) $(PARSE_AI_DIR) $(GENERATED_DIR) $(GENERATED_AI_DIR)

# Step a: Upload files
upload: $(TEST_LOG_DIR)
	@if [ -z "$(FILES)" ]; then \
		echo "📤 Using default files: samples/super_complex_enhanced/*.xml"; \
		echo "📤 Uploading files to $(STAGING_DIR)..."; \
		python scripts/test_flow.py upload --files "samples/super_complex_enhanced/*.xml" --staging-dir $(STAGING_DIR) --api-url $(API_URL); \
	else \
		echo "📤 Uploading files to $(STAGING_DIR)..."; \
		python scripts/test_flow.py upload --files "$(FILES)" --staging-dir $(STAGING_DIR) --api-url $(API_URL); \
	fi

# Step b: Parse mappings
parse: $(TEST_LOG_DIR)
	@echo "🔍 Parsing mappings..."
	@python scripts/test_flow.py parse --staging-dir $(STAGING_DIR) --output-dir $(PARSED_DIR) --api-url $(API_URL)

# Step c: Enhance with AI
enhance: $(TEST_LOG_DIR)
	@echo "🤖 Enhancing parsed models with AI..."
	@python scripts/test_flow.py enhance --parsed-dir $(PARSED_DIR) --output-dir $(PARSE_AI_DIR) --api-url $(API_URL)

# Step d: Generate hierarchy/tree
hierarchy: $(TEST_LOG_DIR)
	@echo "🌳 Generating hierarchy structure..."
	@mkdir -p $(TEST_LOG_DIR)/diagrams
	@python scripts/test_flow.py hierarchy --output-dir $(TEST_LOG_DIR)/diagrams --api-url $(API_URL)

# Step e: Generate lineage diagram
lineage: $(TEST_LOG_DIR)
	@echo "📊 Generating lineage diagrams..."
	@mkdir -p $(TEST_LOG_DIR)/diagrams
	@python scripts/test_flow.py lineage --output-dir $(TEST_LOG_DIR)/diagrams --api-url $(API_URL)

# Step f: Generate canonical model image
canonical: $(TEST_LOG_DIR)
	@echo "🕸️ Generating canonical model visualizations..."
	@mkdir -p $(TEST_LOG_DIR)/diagrams
	@python scripts/test_flow.py canonical --output-dir $(TEST_LOG_DIR)/diagrams --api-url $(API_URL)

# Step g: Generate code
code: $(TEST_LOG_DIR)
	@echo "💻 Generating code (PySpark/DLT/SQL)..."
	@python scripts/test_flow.py code --output-dir $(GENERATED_DIR) --api-url $(API_URL)

# Step h: Review & fix code with AI
review: $(TEST_LOG_DIR)
	@echo "🔍 Reviewing and fixing code with AI..."
	@python scripts/test_flow.py review --generated-dir $(GENERATED_DIR) --output-dir $(GENERATED_AI_DIR) --api-url $(API_URL)

# Step i: Generate diff reports
diff: $(TEST_LOG_DIR)
	@echo "📊 Generating diff reports..."
	@python scripts/utils/generate_diff.py --test-log-dir $(TEST_LOG_DIR) --output-dir $(TEST_LOG_DIR)/diffs

# Run all steps in sequence
test-all: $(TEST_LOG_DIR)
	@echo "🚀 Starting full test sequence (logging to $(TEST_LOG_DIR)/exec_steps_logs.txt)..."
	@mkdir -p $(TEST_LOG_DIR)/diagrams
	@$(MAKE) clean
	@bash -c '$(MAKE) upload parse enhance hierarchy lineage canonical code review diff 2>&1 | tee $(TEST_LOG_DIR)/exec_steps_logs.txt'
	@echo ""
	@echo "✅ All steps completed! Check $(TEST_LOG_DIR) for results."
	@echo "📄 View diff reports: $(TEST_LOG_DIR)/diffs/index.html"
	@echo "📊 View diagrams: $(TEST_LOG_DIR)/diagrams/"
	@if [ -f "$(TEST_LOG_DIR)/exec_steps_logs.txt" ]; then \
		echo "📝 Execution logs saved to: $(TEST_LOG_DIR)/exec_steps_logs.txt ($$(wc -l < $(TEST_LOG_DIR)/exec_steps_logs.txt) lines)"; \
	else \
		echo "⚠️  Warning: Log file was not created"; \
	fi

# Clean test_log directory contents (but keep directory structure)
clean:
	@echo "🧹 Cleaning test_log directory contents..."
	@if [ -d "$(TEST_LOG_DIR)" ]; then \
		find $(TEST_LOG_DIR) -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null || true; \
		find $(TEST_LOG_DIR) -mindepth 1 -maxdepth 1 -type f ! -name ".gitkeep" -delete 2>/dev/null || true; \
		echo "✅ Cleaned test_log directory contents (kept directory structure)"; \
	else \
		echo "ℹ️  test_log directory doesn't exist, nothing to clean"; \
	fi

# Clean test_log directory completely (including directory)
clean-all:
	@echo "🧹 Removing test_log directory completely..."
	rm -rf $(TEST_LOG_DIR)
	@echo "✅ Removed!"

