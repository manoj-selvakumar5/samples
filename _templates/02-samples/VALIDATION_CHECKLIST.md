# Sample Structure Validation Checklist

Use this checklist to ensure your sample follows the best practice structure guidelines.

## General Requirements (All Samples)

### ✅ Required Files
- [ ] README.md exists with comprehensive documentation
- [ ] requirements.txt OR pyproject.toml exists
- [ ] .env.example exists with all required environment variables
- [ ] At least one architecture diagram in `images/` directory
- [ ] No hardcoded credentials in any files
- [ ] No AWS resource names or IDs hardcoded in code

### ✅ Directory Naming
- [ ] Sample directory uses lowercase-with-hyphens format (e.g., `restaurant-assistant/`)
- [ ] Uses `images/` not `Image/` or `IMAGES/`
- [ ] Uses `infrastructure/` for AWS setup (standardized, not `prereqs/`)
- [ ] Uses `src/` for source code modules (if applicable)
- [ ] Uses `config/` for configuration files (if applicable)
- [ ] Uses `data/` for sample data (if applicable)

### ✅ File Naming
- [ ] Python files use snake_case.py
- [ ] Shell scripts use lowercase with underscores (e.g., `deploy_prereqs.sh`)
- [ ] Config files use appropriate format (.env.example, settings.yaml)
- [ ] Image files use lowercase with underscores (e.g., `architecture.png`)

---

## Python-Based Sample Validation

### Minimal Python Sample Checklist
- [ ] Single entry point: `main.py` or `{sample_name}.py`
- [ ] requirements.txt with all dependencies
- [ ] README.md with quick start section
- [ ] Architecture diagram in `images/architecture.png`
- [ ] .env.example with required variables
- [ ] Agent/tool code is clear and self-contained
- [ ] No complex directory structure (flat or minimal nesting)

### Complex Python Sample Checklist
- [ ] Main entry point: `main.py` or `{sample_name}.py`
- [ ] requirements.txt or pyproject.toml
- [ ] README.md with comprehensive sections:
  - [ ] Overview
  - [ ] Architecture explanation
  - [ ] Prerequisites
  - [ ] Installation steps
  - [ ] Usage examples
  - [ ] Configuration details
  - [ ] Project structure diagram
  - [ ] Cleanup instructions
  - [ ] Troubleshooting section
- [ ] Architecture diagrams (multiple if needed)
- [ ] .env.example with all variables documented

#### ✅ Source Code Organization
- [ ] All agents in `src/agents/` directory
  - [ ] Each agent in separate file
  - [ ] `__init__.py` exists
- [ ] All tools in `src/tools/` directory
  - [ ] Organized by functionality if 5+ tools
  - [ ] `__init__.py` exists
- [ ] Utilities in `src/utils/` directory
  - [ ] `constants.py` for constants
  - [ ] `helpers.py` for helper functions
  - [ ] `__init__.py` exists

#### ✅ Infrastructure (if AWS resources used)
- [ ] `infrastructure/` directory exists
- [ ] `infrastructure/deploy_prereqs.sh` script exists
- [ ] `infrastructure/cleanup.sh` script exists
- [ ] `infrastructure/prereqs_config.yaml` exists
- [ ] AWS resource scripts in `infrastructure/aws/`:
  - [ ] `dynamodb.py` (if using DynamoDB)
  - [ ] `s3.py` (if using S3)
  - [ ] `knowledge_base.py` (if using KB)
- [ ] Scripts have proper error handling
- [ ] Scripts check for AWS credentials
- [ ] Cleanup script confirms before deletion

#### ✅ Configuration
- [ ] Configuration files in `config/` directory
- [ ] No sensitive data in config files
- [ ] Environment variables used for secrets

---

## Jupyter Notebook-Based Sample Validation

### Minimal Notebook Sample Checklist
- [ ] Main notebook: `{sample-name}.ipynb` (matches directory name)
- [ ] requirements.txt with all dependencies
- [ ] README.md with quick start
- [ ] Architecture diagram in `images/architecture.png`
- [ ] .env.example with required variables
- [ ] Notebook has clear structure:
  - [ ] Title and introduction (Markdown)
  - [ ] Prerequisites section (Markdown)
  - [ ] Setup/installation cell (Code)
  - [ ] Imports and environment loading (Code)
  - [ ] Tool definitions with explanations (Markdown + Code)
  - [ ] Agent setup with explanations (Markdown + Code)
  - [ ] Usage examples (Code)
  - [ ] Next steps or conclusion (Markdown)

### Complex Notebook Sample Checklist
- [ ] Main notebook: `{sample-name}.ipynb`
- [ ] requirements.txt or pyproject.toml
- [ ] README.md with comprehensive documentation:
  - [ ] Overview
  - [ ] Architecture with diagram
  - [ ] Prerequisites
  - [ ] Installation steps (including AWS setup)
  - [ ] Project structure explanation
  - [ ] Cleanup instructions
  - [ ] What you'll learn section
- [ ] Architecture diagrams (multiple if needed)
- [ ] .env.example with all variables documented

#### ✅ External Source Code (if used)
- [ ] Reusable code in `src/` directory (not in notebook)
- [ ] Agents in `src/agents/` if multiple agents
- [ ] Tools in `src/tools/` if multiple tools
- [ ] Utilities in `src/utils/` for helpers
- [ ] All modules have `__init__.py`
- [ ] Notebook imports from `src/` modules
- [ ] Clear separation: notebook = orchestration, src = implementation

#### ✅ Notebook Structure
- [ ] Logical flow from setup to execution
- [ ] Markdown explanations before code cells
- [ ] Architecture diagram shown early
- [ ] Environment setup at the beginning
- [ ] Clear section headers (Markdown)
- [ ] Example outputs shown
- [ ] Cleanup instructions at end (commented out)

#### ✅ Infrastructure (if AWS resources used)
- [ ] `infrastructure/` directory exists
- [ ] `infrastructure/deploy_prereqs.sh` script exists
- [ ] `infrastructure/cleanup.sh` script exists
- [ ] `infrastructure/prereqs_config.yaml` exists
- [ ] AWS resource scripts in `infrastructure/aws/`
- [ ] Notebook includes cell to run deployment script
- [ ] Notebook includes cell to run cleanup (commented)

#### ✅ Data Files (if used)
- [ ] Sample data in `data/` directory
- [ ] Data files are sample/test data only (not production)
- [ ] Data files referenced in notebook with clear explanations

---

## README.md Content Validation

### ✅ Required Sections
- [ ] Title (# Sample Name)
- [ ] Overview/Description
- [ ] Architecture diagram embedded
- [ ] Prerequisites listed
- [ ] Installation/Setup instructions
- [ ] Usage instructions or examples
- [ ] Configuration section (environment variables)

### ✅ Recommended Sections
- [ ] Key Features list
- [ ] Use Cases
- [ ] Architecture explanation
- [ ] Project structure tree
- [ ] Cleanup instructions (if AWS used)
- [ ] Troubleshooting section
- [ ] Related samples
- [ ] What you'll learn (for notebooks)

---

## .env.example Validation

### ✅ Required Content
- [ ] All environment variables documented
- [ ] Each variable has a comment explaining purpose
- [ ] Default values provided where applicable
- [ ] No actual credentials (use placeholders)
- [ ] Groups related variables together

### Example Format:
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# Bedrock Model
MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# API Keys (replace with your keys)
# API_KEY=your_api_key_here

# AWS Resources (set after deployment)
# DYNAMODB_TABLE_NAME=your-table-name
# S3_BUCKET_NAME=your-bucket-name
```

---

## Architecture Diagram Validation

### ✅ Diagram Requirements
- [ ] At least one diagram exists in `images/` directory
- [ ] Main diagram named `architecture.png`
- [ ] Diagram shows agent interactions
- [ ] Diagram shows data flow
- [ ] Diagram shows external dependencies (AWS, APIs)
- [ ] Diagram is clear and readable
- [ ] Diagram embedded in README.md

### ✅ Complex Samples (additional diagrams)
- [ ] `agent_flow.png` for multi-agent workflows
- [ ] `system_design.png` for system architecture
- [ ] `workflow.png` for step-by-step processes

---

## Code Quality Validation

### ✅ Python Code
- [ ] Docstrings for all functions/classes
- [ ] Type hints used appropriately
- [ ] Clear variable and function names
- [ ] No commented-out code blocks
- [ ] Error handling implemented
- [ ] Logging used for important operations
- [ ] No print statements for debugging (use logging)

### ✅ Imports
- [ ] Standard library imports first
- [ ] Third-party imports second
- [ ] Local/project imports last
- [ ] No unused imports
- [ ] Imports organized alphabetically within groups

### ✅ Tools and Agents
- [ ] Tools have clear descriptions
- [ ] Tool parameters have type hints
- [ ] Agent system prompts are clear and specific
- [ ] Agent configurations are well-documented

---

## Infrastructure Scripts Validation

### ✅ deploy_prereqs.sh
- [ ] Has shebang: `#!/bin/bash`
- [ ] Has `set -e` for error handling
- [ ] Uses color output for clarity
- [ ] Checks for AWS credentials before running
- [ ] Validates config file exists
- [ ] Provides clear status messages
- [ ] Returns error codes appropriately

### ✅ cleanup.sh
- [ ] Has shebang: `#!/bin/bash`
- [ ] Has `set -e` for error handling
- [ ] Uses color output for clarity
- [ ] Asks for confirmation before deletion
- [ ] Deletes resources in reverse order
- [ ] Handles errors gracefully (|| true)
- [ ] Provides clear status messages

### ✅ AWS Resource Scripts (Python)
- [ ] Reads from prereqs_config.yaml
- [ ] Supports --delete flag for cleanup
- [ ] Has error handling
- [ ] Prints resource ARNs/IDs after creation
- [ ] Checks if resources already exist
- [ ] Uses boto3 properly

---

## Security Validation

### ✅ Secrets Management
- [ ] No hardcoded AWS credentials
- [ ] No hardcoded API keys
- [ ] No hardcoded passwords
- [ ] All secrets in environment variables
- [ ] .env file in .gitignore (project-level)

### ✅ AWS Resources
- [ ] No hardcoded resource names
- [ ] No hardcoded ARNs or IDs
- [ ] Resources use environment variables or config files
- [ ] IAM permissions documented in README

---

## Testing Validation (Optional but Recommended)

### ✅ Manual Testing
- [ ] Fresh install tested (new virtual environment)
- [ ] All dependencies install correctly
- [ ] Sample runs without errors
- [ ] All examples in README work
- [ ] Cleanup script successfully removes resources
- [ ] Instructions are clear and complete

### ✅ Automated Testing (Advanced)
- [ ] Unit tests for tools in `tests/`
- [ ] Integration tests for agents
- [ ] CI/CD pipeline configured
- [ ] Tests pass in clean environment

---

## Common Issues Checklist

### ❌ Common Mistakes to Avoid
- [ ] **Not Fixed**: Mixed case directory names (Image/ instead of images/)
- [ ] **Not Fixed**: Python code in root instead of src/
- [ ] **Not Fixed**: Hardcoded credentials in code
- [ ] **Not Fixed**: Missing architecture diagrams
- [ ] **Not Fixed**: No .env.example file
- [ ] **Not Fixed**: Missing cleanup scripts for AWS
- [ ] **Not Fixed**: README doesn't match actual structure
- [ ] **Not Fixed**: Incomplete installation instructions
- [ ] **Not Fixed**: No error handling in scripts
- [ ] **Not Fixed**: Using `prereqs/` instead of `infrastructure/`

---

## Structure Complexity Decision

### Should I use Minimal or Complex?

**Use Minimal Structure if:**
- [ ] Single agent only
- [ ] 0-2 custom tools
- [ ] No AWS resources OR simple setup
- [ ] Self-contained functionality
- [ ] Quick demonstration

**Use Complex Structure if:**
- [ ] 3+ agents (multi-agent system)
- [ ] 5+ custom tools
- [ ] AWS infrastructure required
- [ ] Reusable modules needed
- [ ] Production-ready patterns

---

## Final Validation

### Before Submission
- [ ] Ran through entire checklist
- [ ] Tested installation from scratch
- [ ] README accurately reflects structure
- [ ] All links in README work
- [ ] Architecture diagrams are up-to-date
- [ ] .env.example has all required variables
- [ ] Cleanup script tested and works
- [ ] No TODO comments left in code
- [ ] Code is formatted consistently
- [ ] Sample added to parent README.md (02-samples/README.md)

---

## Quick Validation Command

Run this to check basic structure:
```bash
# Check required files exist
ls README.md requirements.txt .env.example images/architecture.png

# Check directory naming (should be lowercase)
find . -type d -name "*[A-Z]*" | grep -v ".git\|venv\|node_modules"

# Check for hardcoded credentials
grep -r "aws_access_key\|aws_secret\|password\|api_key" --include="*.py" --include="*.ipynb" .

# Check imports organization (Python files)
find . -name "*.py" -exec python -m isort --check-only {} \;
```

---

## Validation Summary

- **Total Essential Items**: ~50
- **Total Recommended Items**: ~20
- **Minimum Pass Rate**: 100% of essential items
- **Target Pass Rate**: 90% of all items

**Validation Status**:
- [ ] ✅ All essential items pass
- [ ] ✅ 90%+ of recommended items pass
- [ ] ✅ Ready for submission
