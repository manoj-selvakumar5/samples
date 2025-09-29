# Best Practice Tutorial Structure Template

Based on analysis of existing tutorials, this is the optimal structure for tutorials in `01-tutorials`:

## Recommended Directory Structure

### Minimal Structure (Simple Tutorial)
```
tutorial-name/
├── notebook.ipynb                   # Main tutorial notebook
├── requirements.txt                 # Python dependencies
└── images/                          # Diagrams and screenshots
    └── architecture.png
```

### Standard Structure (Most Common)
```
tutorial-name/
├── notebook.ipynb                   # Main tutorial notebook
├── requirements.txt                 # Python dependencies
├── README.md                        # Tutorial overview and instructions
├── images/                          # Diagrams and screenshots
│   └── architecture.png
├── src/                             # Source code (if needed)
│   ├── tools.py                     # Custom tool implementations
│   └── utils.py                     # Helper functions
└── config/                          # Configuration files
    └── .env.example                 # Environment variables template
```

### Full Structure (Complex Tutorial with AWS)
```
tutorial-name/
├── notebook.ipynb                   # Main tutorial notebook
├── requirements.txt                 # Python dependencies
├── README.md                        # Tutorial overview and instructions
├── images/                          # Diagrams and screenshots
│   ├── architecture.png
│   └── flow_diagram.png
├── src/                             # Source code
│   ├── __init__.py                 # Package initialization
│   ├── tools/                      # Tool implementations
│   │   ├── __init__.py
│   │   ├── custom_tool.py          # @tool decorator implementation
│   │   └── tool_spec.py            # TOOL_SPEC implementation
│   ├── agents/                     # Agent configurations
│   │   └── agent_config.py
│   └── utils/                      # Utility functions
│       └── helpers.py
├── scripts/                         # Executable scripts
│   ├── setup.sh                    # Environment setup
│   └── cleanup.sh                  # Resource cleanup
├── infrastructure/                  # Infrastructure as code
│   ├── deploy.sh                   # Deployment script
│   ├── config.yaml                 # Infrastructure configuration
│   └── aws/                        # AWS-specific resources
│       ├── dynamodb.py
│       ├── s3.py
│       └── knowledge_base.py
├── data/                           # Sample data and resources
│   ├── sample_input.json
│   └── test_data.csv
└── config/                         # Configuration files
    ├── .env.example                # Environment variables template
    └── settings.yaml               # Application settings
```

## When to Use Each Structure

### Use Minimal Structure When:
- Tutorial focuses on a single concept
- No custom tools or external services needed
- Quick demonstration or proof of concept
- Learning objective is straightforward

### Use Standard Structure When:
- Tutorial includes 1-3 custom tools
- Need environment configuration
- Multiple related concepts being taught
- Requires clear documentation beyond notebook

### Use Full Structure When:
- Complex multi-component tutorial
- AWS or external service integration
- Multiple agents or orchestration
- Production-ready patterns being demonstrated
- Requires infrastructure setup/teardown

## Directory Organization Principles

### 1. **Separation of Concerns**
```
src/          # All Python source code
scripts/      # Bash/shell executables
config/       # Configuration files
data/         # Static data and samples
images/       # Visual assets
infrastructure/ # IaC and deployment
```

### 2. **Naming Conventions**
- **Directories**: Use lowercase with underscores or hyphens
- **Python files**: Use snake_case (e.g., `custom_tool.py`)
- **Scripts**: Use lowercase with hyphens (e.g., `deploy-resources.sh`)
- **Config files**: Use lowercase with dots (e.g., `.env.example`)

### 3. **File Placement Rules**
- **Single tool**: Place in `src/tools.py`
- **Multiple tools (2-5)**: Separate files in `src/tools/`
- **Many tools (>5)**: Organize by functionality in subdirectories
- **AWS resources**: Always in `infrastructure/aws/`
- **Helper functions**: Always in `src/utils/`

## File Templates

### 1. Main Notebook Structure (tutorial-name.ipynb)
Follow the standardized structure from NOTEBOOK_STANDARDIZATION_GUIDE.md

### 2. requirements.txt
```txt
strands-agents>=0.1.0
strands-tools>=0.1.0
boto3>=1.35.0
pandas>=2.0.0
python-dotenv>=1.0.0
```

### 3. README.md
```markdown
# Tutorial Name

## Overview
Brief description of what this tutorial teaches and why it's important.

## Learning Objectives
By completing this tutorial, you will learn:
- How to [specific skill 1]
- How to [specific skill 2]
- Best practices for [specific topic]

## Prerequisites
- Python 3.10+
- AWS Account with appropriate permissions
- Completed tutorials: F1-first-agent (if dependencies exist)

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Set up AWS resources (if needed)
bash deploy_prereqs.sh

# Open the notebook
jupyter notebook tutorial-name.ipynb
```

## Files Description
- `tutorial-name.ipynb` - Main tutorial notebook with step-by-step instructions
- `tool_name.py` - Custom tool implementation for [purpose]
- `prereqs/` - AWS resource setup scripts
- `images/` - Architecture diagrams and screenshots

## Clean Up
After completing the tutorial:
```bash
bash cleanup.sh
```

## Next Steps
- Proceed to: [Next Tutorial Name]
- Related tutorials: [Related Tutorial]
```

### 4. Source Code Organization (src/)

#### src/tools.py (Single Tool)
```python
"""Custom tool implementations for the tutorial."""

from strands import tool
from typing import Optional

@tool
def process_data(input_text: str, option: Optional[str] = None) -> str:
    """
    Process input data according to specified option.

    Args:
        input_text: The text to process
        option: Processing option (optional)

    Returns:
        Processed text result
    """
    if not input_text:
        return "No input provided"

    # Core logic here
    result = f"Processed: {input_text}"
    if option:
        result += f" with option: {option}"

    return result
```

#### src/tools/custom_tool.py (Multiple Tools)
```python
"""Individual tool module when multiple tools exist."""

from strands.types.tools import ToolResult, ToolUse
from typing import Any

TOOL_SPEC = {
    "name": "custom_action",
    "description": "Perform a custom action",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform"
                }
            },
            "required": ["action"]
        }
    }
}

def custom_action(tool: ToolUse, **kwargs: Any) -> ToolResult:
    """Execute the custom action."""
    tool_use_id = tool["toolUseId"]
    action = tool["input"]["action"]

    try:
        # Implementation
        result = f"Executed: {action}"
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": result}]
        }
    except Exception as e:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": str(e)}]
        }
```

### 5. Scripts Organization

#### scripts/setup.sh
```bash
#!/bin/bash
set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up tutorial environment...${NC}"

# Check Python version
if ! python3 --version | grep -E "3\.(10|11|12)" > /dev/null; then
    echo -e "${RED}Error: Python 3.10+ is required${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Set up environment variables
if [ ! -f ".env" ] && [ -f "config/.env.example" ]; then
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cp config/.env.example .env
    echo -e "${YELLOW}Please update .env with your configuration${NC}"
fi

echo -e "${GREEN}Setup complete!${NC}"
```

#### scripts/cleanup.sh
```bash
#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Cleaning up tutorial resources...${NC}"

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Clean Jupyter checkpoints
find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true

# Remove data outputs (optional)
if [ -d "output" ]; then
    echo -e "${YELLOW}Removing output directory...${NC}"
    rm -rf output/
fi

echo -e "${GREEN}Cleanup complete!${NC}"
```

### 6. Infrastructure Configuration

#### infrastructure/config.yaml
```yaml
# Infrastructure configuration
project:
  name: tutorial-project
  environment: development
  region: ${AWS_REGION:-us-east-1}

resources:
  # AWS resources (if needed)
  dynamodb:
    enabled: false
    tables: []

  s3:
    enabled: false
    buckets: []

  # External services
  external:
    enabled: false
    services: []
```

#### infrastructure/deploy.sh
```bash
#!/bin/bash
set -e

# Load configuration
CONFIG_FILE="infrastructure/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Parse YAML and deploy resources
echo "Deploying infrastructure..."

# Check if AWS resources are needed
if grep -q "enabled: true" "$CONFIG_FILE"; then
    echo "Deploying AWS resources..."
    python infrastructure/aws/deploy.py
fi

echo "Infrastructure deployment complete!"
```

## Quick Decision Tree

```
Does your tutorial need custom tools?
├── No → Use MINIMAL structure
├── Yes (1-3 tools) → Use STANDARD structure
└── Yes (4+ tools or AWS) → Use FULL structure

Does it need AWS resources?
├── No → Keep scripts simple
├── Yes (1-2 services) → Add infrastructure/deploy.sh
└── Yes (3+ services) → Use full infrastructure/ directory

Does it have multiple concepts?
├── No → Single notebook
├── Yes (related) → Single notebook with sections
└── Yes (distinct) → Consider splitting into sub-tutorials
```

## Best Practices

### Structure DO's:
✅ Start with minimal structure, expand as needed
✅ Use `src/` for all Python code (cleaner root)
✅ Use `scripts/` for all bash scripts
✅ Use `config/` for all configuration files
✅ Keep `images/` flat (no subdirectories)
✅ Include README only if adds value beyond notebook

### Structure DON'Ts:
❌ Don't create directories with single files
❌ Don't mix Python and bash scripts in root
❌ Don't nest more than 2 levels deep
❌ Don't duplicate configuration across files

### Code Organization:
✅ One tool = one function in `src/tools.py`
✅ Multiple tools = separate files in `src/tools/`
✅ Shared logic = `src/utils/helpers.py`
✅ Agent configs = `src/agents/config.py`
✅ Constants = `config/settings.yaml`

### Naming Standards:
✅ Directories: `lowercase-hyphen` or `lowercase_underscore`
✅ Python files: `snake_case.py`
✅ Scripts: `action-verb.sh` (e.g., `setup-env.sh`)
✅ Notebooks: `descriptive-name.ipynb`
✅ Config: `.env.example`, `config.yaml`

## Example: Well-Structured Tutorial

### 08-observability-and-evaluation/
This tutorial exemplifies the best structure:
- Clear separation of tools as individual files
- Comprehensive prereqs folder for AWS setup
- Both deploy and cleanup scripts
- Well-organized data files
- Clean, descriptive naming

## Naming Conventions

### Tutorial Folders
- Use sequential numbering: 01-, 02-, 03-
- Use descriptive kebab-case: `observability-and-evaluation`
- Full pattern: `08-observability-and-evaluation/`

### Files
- **Notebooks**: `descriptive-name.ipynb`
- **Python tools**: `action_object.py` (e.g., `create_booking.py`, `delete_booking.py`)
- **Scripts**: `deploy_prereqs.sh`, `cleanup.sh`
- **Config**: `prereqs_config.yaml`

## Migration Guide for Existing Tutorials

To update existing tutorials to this structure:

1. **Assess current structure** - Identify which template fits best
2. **Create directories** - Add `src/`, `scripts/`, `config/` as needed
3. **Move files**:
   - Python files → `src/` or `src/tools/`
   - Shell scripts → `scripts/`
   - Config files → `config/`
   - AWS setup → `infrastructure/`
4. **Update imports** - Fix Python import paths
5. **Test everything** - Ensure notebook still runs

## Checklist for New Tutorials

### Essential (Must Have):
- [ ] Main notebook following standard sections
- [ ] requirements.txt with pinned versions
- [ ] Architecture diagram (if multi-component)
- [ ] No hardcoded credentials or secrets

### Standard (Should Have):
- [ ] README.md if complex setup needed
- [ ] Source code in `src/` directory
- [ ] Scripts in `scripts/` directory
- [ ] Config in `config/` directory
- [ ] .env.example for environment variables

### Advanced (Nice to Have):
- [ ] Infrastructure as code in `infrastructure/`
- [ ] Automated setup/cleanup scripts
- [ ] Unit tests for custom tools
- [ ] Performance benchmarks
- [ ] Alternative implementations

## Common Pitfalls to Avoid

1. **Flat structure with many files** → Use directories to organize
2. **Deep nesting** → Keep max 2 levels deep
3. **Mixed concerns** → Separate code, config, scripts
4. **Unclear dependencies** → Document in README
5. **Missing cleanup** → Always provide cleanup for resources
6. **Hardcoded paths** → Use relative paths or config files