# Best Practice Sample Structure Template

This guide provides standardized directory structures for samples in `02-samples`, covering both Python-based and Jupyter Notebook-based samples.

## Structure Options

### Python-Based Samples

#### Minimal Structure (Simple Python Sample)
```
sample-name/
├── main.py or sample_name.py        # Main agent/application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # Sample overview and setup
├── images/                          # Architecture diagrams
│   └── architecture.png
└── .env.example                     # Environment variables template
```

**Use when:**
- Simple, single-agent demonstration
- No AWS resources
- 1-2 custom tools maximum
- Self-contained functionality

#### Complex Structure (Multi-Agent Python Sample)
```
sample-name/
├── main.py or sample_name.py        # Main orchestrator/entry point
├── requirements.txt or pyproject.toml
├── README.md                        # Comprehensive documentation
├── .env.example                     # Environment variables template
├── images/                          # Architecture diagrams
│   ├── architecture.png
│   └── agent_flow.png
├── src/                             # Source code modules
│   ├── __init__.py
│   ├── agents/                      # Multiple agent implementations
│   │   ├── __init__.py
│   │   ├── coordinator_agent.py
│   │   ├── specialist_agent_1.py
│   │   └── specialist_agent_2.py
│   ├── tools/                       # Custom tools
│   │   ├── __init__.py
│   │   ├── tool_category_1/
│   │   │   ├── __init__.py
│   │   │   └── specific_tool.py
│   │   └── tool_category_2/
│   │       ├── __init__.py
│   │       └── another_tool.py
│   └── utils/                       # Utilities and helpers
│       ├── __init__.py
│       ├── constants.py
│       └── helpers.py
├── infrastructure/                  # Infrastructure as code
│   ├── deploy_prereqs.sh
│   ├── cleanup.sh
│   ├── prereqs_config.yaml
│   └── aws/                         # AWS resource setup
│       ├── dynamodb.py
│       ├── s3.py
│       └── knowledge_base.py
├── config/                          # Configuration files
│   └── settings.yaml
└── data/                            # Sample and test data
    ├── sample_inputs/
    └── test_data/
```

**Use when:**
- Multi-agent system (3+ agents)
- AWS infrastructure dependencies
- Many custom tools (5+)
- Production-ready patterns
- Requires setup/teardown scripts

---

### Jupyter Notebook-Based Samples

#### Minimal Structure (Simple Notebook Sample)
```
sample-name/
├── sample-name.ipynb                # Main tutorial notebook
├── requirements.txt                 # Python dependencies
├── README.md                        # Quick start and overview
├── images/                          # Architecture diagrams
│   └── architecture.png
└── .env.example                     # Environment variables template
```

**Use when:**
- Educational/demonstration focused
- Step-by-step walkthrough
- No AWS resources or simple setup
- 1-2 custom tools (can be in notebook)
- Interactive exploration

#### Complex Structure (Advanced Notebook Sample)
```
sample-name/
├── sample-name.ipynb                # Main tutorial notebook
├── requirements.txt                 # Python dependencies
├── README.md                        # Setup guide and overview
├── .env.example                     # Environment variables template
├── images/                          # Architecture diagrams
│   ├── architecture.png
│   └── workflow.png
├── src/                             # External source code
│   ├── __init__.py
│   ├── agents/                      # Agent implementations
│   │   ├── __init__.py
│   │   └── specialized_agent.py
│   ├── tools/                       # Custom tool implementations
│   │   ├── __init__.py
│   │   ├── tool_1.py
│   │   └── tool_2.py
│   └── utils/                       # Helper functions
│       ├── __init__.py
│       └── helpers.py
├── infrastructure/                  # Infrastructure setup
│   ├── deploy_prereqs.sh
│   ├── cleanup.sh
│   ├── prereqs_config.yaml
│   └── aws/                         # AWS resources
│       ├── dynamodb.py
│       ├── s3.py
│       └── knowledge_base.py
├── config/                          # Configuration files
│   └── settings.yaml
└── data/                            # Sample data
    └── sample_input.json
```

**Use when:**
- Complex multi-step tutorial
- AWS infrastructure required
- Multiple external modules needed
- Reusable tools/agents across cells
- Data preprocessing required
- Deployment/cleanup scripts needed

---

## Detailed Templates

### 1. Minimal Python Sample

#### main.py
```python
"""
Sample Name - Brief description.

This sample demonstrates [key features].
"""

import os
from dotenv import load_dotenv
from strands.agents import Agent
from strands.tools import tool

load_dotenv()

@tool
def custom_action(parameter: str) -> str:
    """
    Description of what this tool does.

    Args:
        parameter: Description

    Returns:
        Result description
    """
    return f"Result: {parameter}"

# Configure agent
agent = Agent(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    system_prompt="You are a helpful assistant that...",
    tools=[custom_action]
)

def main():
    """Main execution function."""
    print("Starting Sample Agent...")
    response = agent.run("User query")
    print(response)

if __name__ == "__main__":
    main()
```

#### README.md (Minimal Python)
```markdown
# Sample Name

Brief description and purpose.

![Architecture](images/architecture.png)

## Prerequisites
- Python 3.10+
- AWS credentials (if applicable)

## Quick Start
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python main.py
```

## Usage
Describe how to use the sample.

## Configuration
List environment variables needed.
```

---

### 2. Complex Python Sample

#### main.py (Complex)
```python
"""
Sample Name - Multi-agent orchestration system.

This sample demonstrates coordinated multi-agent collaboration.
"""

import os
from dotenv import load_dotenv
from src.agents.coordinator_agent import CoordinatorAgent
from src.agents.specialist_agent_1 import SpecialistAgent1
from src.agents.specialist_agent_2 import SpecialistAgent2
from src.utils.constants import DEFAULT_MODEL

load_dotenv()

class SampleOrchestrator:
    """Main orchestrator for the multi-agent system."""

    def __init__(self):
        """Initialize all agents."""
        self.coordinator = CoordinatorAgent(model=DEFAULT_MODEL)
        self.specialist_1 = SpecialistAgent1(model=DEFAULT_MODEL)
        self.specialist_2 = SpecialistAgent2(model=DEFAULT_MODEL)

    def run(self, task: str) -> str:
        """
        Execute task using coordinated agents.

        Args:
            task: The task to execute

        Returns:
            Final result from agent collaboration
        """
        plan = self.coordinator.plan(task)

        if plan["use_specialist_1"]:
            result = self.specialist_1.execute(task)
        else:
            result = self.specialist_2.execute(task)

        return self.coordinator.synthesize(result)

def main():
    """Main execution function."""
    print("Starting Multi-Agent Sample...")
    orchestrator = SampleOrchestrator()
    result = orchestrator.run("Sample task")
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

#### README.md (Complex Python)
```markdown
# Sample Name

## Overview
Comprehensive description of what this sample demonstrates.

![Architecture Diagram](images/architecture.png)

## Key Features
- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Architecture
Detailed explanation of system architecture, agent interactions, and data flow.

### Components
- **Coordinator Agent**: Plans and delegates tasks
- **Specialist Agent 1**: Handles X tasks
- **Specialist Agent 2**: Handles Y tasks

## Prerequisites
- Python 3.10+
- AWS Account with appropriate permissions
- Required API keys

## Installation

### 1. Set Up Environment
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### 2. Deploy AWS Resources
```bash
bash infrastructure/deploy_prereqs.sh
```

## Usage

### Basic Usage
```bash
python main.py
```

### Advanced Usage
```python
from main import SampleOrchestrator
orchestrator = SampleOrchestrator()
result = orchestrator.run("Your task")
```

## Configuration

### Environment Variables
- `AWS_REGION`: AWS region
- `MODEL_ID`: Bedrock model ID

### Configuration Files
- `config/settings.yaml`: General settings

## Project Structure
```
sample-name/
├── main.py                    # Main entry point
├── src/                       # Source code
│   ├── agents/               # Agent implementations
│   ├── tools/                # Custom tools
│   └── utils/                # Utilities
└── infrastructure/           # AWS setup
```

## Clean Up
```bash
bash infrastructure/cleanup.sh
```

## Troubleshooting
Common issues and solutions.
```

---

### 3. Minimal Notebook Sample

#### sample-name.ipynb Structure
```
Cell 1 (Markdown):
# Sample Name
Brief description and what you'll learn.

Cell 2 (Markdown):
## Prerequisites
- Required packages
- API keys needed

Cell 3 (Code):
# Install dependencies
!pip install -r requirements.txt

Cell 4 (Code):
# Load environment and imports
import os
from dotenv import load_dotenv
from strands.agents import Agent
load_dotenv()

Cell 5 (Markdown):
## Define Custom Tool
Explanation of the tool

Cell 6 (Code):
# Tool implementation
from strands.tools import tool

@tool
def custom_action(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"

Cell 7 (Markdown):
## Create Agent
Explanation of agent setup

Cell 8 (Code):
# Configure agent
agent = Agent(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    system_prompt="You are...",
    tools=[custom_action]
)

Cell 9 (Markdown):
## Run Sample
Test the agent

Cell 10 (Code):
# Execute
response = agent.run("Sample query")
print(response)

Cell 11 (Markdown):
## Next Steps
What to explore next
```

#### README.md (Minimal Notebook)
```markdown
# Sample Name

Brief description.

![Architecture](images/architecture.png)

## Quick Start
```bash
pip install -r requirements.txt
cp .env.example .env
jupyter notebook sample-name.ipynb
```

## What You'll Learn
- Learning objective 1
- Learning objective 2

## Prerequisites
- Python 3.10+
- Jupyter Notebook
```

---

### 4. Complex Notebook Sample

#### sample-name.ipynb Structure
```
Cell 1 (Markdown):
# Sample Name
Comprehensive introduction and learning objectives.

Cell 2 (Markdown):
## Architecture Overview
![Architecture](images/architecture.png)
Explanation of the system.

Cell 3 (Markdown):
## Setup
Prerequisites and installation steps.

Cell 4 (Code):
# Install dependencies
!pip install -r requirements.txt

Cell 5 (Code):
# Deploy AWS resources (if needed)
!bash infrastructure/deploy_prereqs.sh

Cell 6 (Code):
# Load environment and imports
import os
from dotenv import load_dotenv
from src.agents.coordinator_agent import CoordinatorAgent
from src.agents.specialist_agent_1 import SpecialistAgent1
from src.tools.custom_tool import custom_action

load_dotenv()

Cell 7 (Markdown):
## Agent Configuration
Explanation of multi-agent setup.

Cell 8 (Code):
# Initialize agents
coordinator = CoordinatorAgent(model=os.getenv("MODEL_ID"))
specialist_1 = SpecialistAgent1(model=os.getenv("MODEL_ID"))

Cell 9 (Markdown):
## Example 1: Simple Task
Description of first example.

Cell 10 (Code):
# Execute example 1
result = coordinator.plan("Task description")
print(result)

Cell 11 (Markdown):
## Example 2: Complex Task
Description of second example.

Cell 12 (Code):
# Execute example 2
result = specialist_1.execute("Complex task")
print(result)

Cell 13 (Markdown):
## Cleanup
Remove deployed resources.

Cell 14 (Code):
# Cleanup (optional - uncomment to run)
# !bash infrastructure/cleanup.sh
```

#### README.md (Complex Notebook)
```markdown
# Sample Name

## Overview
Comprehensive description of the multi-agent system.

![Architecture](images/architecture.png)

## Key Features
- Multi-agent orchestration
- AWS service integration
- Custom tool implementations

## Prerequisites
- Python 3.10+
- Jupyter Notebook
- AWS Account

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Deploy AWS Resources
```bash
bash infrastructure/deploy_prereqs.sh
```

### 4. Open Notebook
```bash
jupyter notebook sample-name.ipynb
```

## Project Structure
```
sample-name/
├── sample-name.ipynb          # Main notebook
├── src/                       # External modules
│   ├── agents/               # Agent implementations
│   ├── tools/                # Custom tools
│   └── utils/                # Utilities
└── infrastructure/           # AWS setup scripts
```

## Clean Up
After completing the sample:
```bash
bash infrastructure/cleanup.sh
```

## What You'll Learn
- How to orchestrate multiple agents
- AWS service integration patterns
- Custom tool development
```

---

## Naming Conventions

### Directories
- Use lowercase with hyphens: `sample-name/`
- Standard subdirectories: `src/`, `images/`, `infrastructure/`, `config/`, `data/`

### Files
- **Python entry**: `main.py` or `sample_name.py`
- **Notebook**: `sample-name.ipynb` (matches directory name)
- **Python modules**: `snake_case.py`
- **Scripts**: `deploy_prereqs.sh`, `cleanup.sh`
- **Config**: `.env.example`, `settings.yaml`, `prereqs_config.yaml`
- **Images**: `architecture.png`, `agent_flow.png` (lowercase)

---

## Required Files

### All Samples Must Have:
- ✅ README.md with setup instructions
- ✅ requirements.txt or pyproject.toml
- ✅ .env.example for environment variables
- ✅ Architecture diagram in `images/`
- ✅ No hardcoded credentials

### AWS-Integrated Samples Must Have:
- ✅ `infrastructure/deploy_prereqs.sh`
- ✅ `infrastructure/cleanup.sh`
- ✅ `infrastructure/prereqs_config.yaml`
- ✅ AWS resource scripts in `infrastructure/aws/`

---

## Decision Tree

### Should I use Python or Notebook format?

**Use Python-based structure when:**
- Production-ready code sample
- Command-line execution
- API/service integration
- Automated workflows
- Performance critical

**Use Notebook-based structure when:**
- Educational/tutorial focus
- Step-by-step explanation needed
- Interactive exploration
- Data visualization
- Experimentation encouraged

### Should I use Minimal or Complex structure?

**Use Minimal when:**
- Single agent
- 0-2 custom tools
- No AWS resources
- Self-contained in one file
- Quick demonstration

**Use Complex when:**
- 3+ agents
- 5+ custom tools
- AWS infrastructure needed
- Reusable modules required
- Production patterns shown

---

## Common Files Templates

### .env.example
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# Bedrock Model
MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# AWS Resources (if deployed)
# DYNAMODB_TABLE_NAME=sample-table
# S3_BUCKET_NAME=sample-bucket
# KNOWLEDGE_BASE_ID=kb-id
```

### requirements.txt
```txt
strands-agents>=0.1.0
strands-tools>=0.1.0
boto3>=1.35.0
python-dotenv>=1.0.0
```

### infrastructure/deploy_prereqs.sh
```bash
#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Deploying AWS prerequisites...${NC}"

# Check AWS credentials
aws sts get-caller-identity &> /dev/null || {
    echo "Error: AWS credentials not configured"
    exit 1
}

# Deploy resources
echo -e "${YELLOW}Deploying DynamoDB...${NC}"
python infrastructure/aws/dynamodb.py

echo -e "${GREEN}Deployment complete!${NC}"
```

### infrastructure/cleanup.sh
```bash
#!/bin/bash
set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}Cleaning up AWS resources...${NC}"

read -p "Delete all resources? (y/N): " -n 1 -r
echo
[[ $REPLY =~ ^[Yy]$ ]] || exit 0

python infrastructure/aws/dynamodb.py --delete

echo -e "${GREEN}Cleanup complete!${NC}"
```

---

## Best Practices Summary

### DO:
✅ Match structure to complexity (don't over-engineer)
✅ Use `src/` for all reusable Python modules
✅ Use `infrastructure/` for AWS setup
✅ Include architecture diagrams
✅ Provide cleanup scripts
✅ Follow naming conventions
✅ Include comprehensive README

### DON'T:
❌ Mix notebook and Python as dual entry points
❌ Hardcode credentials or resource names
❌ Omit .env.example
❌ Skip architecture diagrams
❌ Deploy resources without cleanup
❌ Use inconsistent directory naming
❌ Create deep nesting (>3 levels)
