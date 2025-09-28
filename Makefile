# CDP Ninja Build System

.PHONY: docs clean build install test help

# Generate API documentation from JSDoc comments
docs:
	@echo "🥷 Generating API documentation from JSDoc comments..."
	python3 scripts/extract_docs.py
	@echo "✅ Documentation generated in docs/usage/"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Build package
build: clean docs
	@echo "📦 Building CDP Ninja package..."
	python3 -m build

# Install in development mode
install:
	@echo "⚙️ Installing CDP Ninja in development mode..."
	pip install -e .

# Run tests
test:
	@echo "🧪 Running tests..."
	python3 -m pytest tests/ -v

# Show help
help:
	@echo "🥷 CDP Ninja Build System"
	@echo "========================"
	@echo ""
	@echo "Available targets:"
	@echo "  docs    - Generate API documentation from JSDoc comments"
	@echo "  build   - Build package (includes docs generation)"
	@echo "  clean   - Clean build artifacts"
	@echo "  install - Install in development mode"
	@echo "  test    - Run tests"
	@echo "  help    - Show this help"
	@echo ""
	@echo "Examples:"
	@echo "  make docs   # Generate docs from 65+ endpoint JSDoc comments"
	@echo "  make build  # Full build with docs generation"

# Default target
.DEFAULT_GOAL := help