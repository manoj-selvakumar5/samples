# Jupyter Notebook Standardization Guide

## Overview
This guide provides comprehensive standardization guidelines for Jupyter notebooks across the tutorials, samples, integrations, and agentic-rag directories. Following these standards ensures consistency, improves readability, and makes it easier for users to navigate and understand examples.

## Directory Structure Analysis

### Current Organization
```
samples/
├── 01-tutorials/       # Learning-focused, educational progression
├── 02-samples/         # Complete real-world applications
├── 03-integrations/    # External service integrations
├── 04-UX-demos/        # UI/UX demonstrations
└── 05-agentic-rag/     # Advanced RAG patterns
```

## Standardized Notebook Structure

Every Jupyter notebook should follow this consistent section order:

### 1. Title Section
- Clear, descriptive title as H1 header
- Brief one-line description if needed

### 2. Overview
- 2-3 paragraph description of what the notebook accomplishes
- Target audience and use case
- Learning objectives (for tutorials)

### 3. Agent/Feature Details Table
Standard table format:
```markdown
|Feature             |Description                                        |
|--------------------|---------------------------------------------------|
|Native tools used   |current_time, retrieve, calculator                 |
|Custom tools created|create_booking, get_booking_details               |
|Agent Structure     |Single agent architecture                          |
|AWS services used   |Amazon Bedrock, DynamoDB, S3                      |
```

### 4. Architecture Diagram
- Located in `images/` or `assets/` subfolder
- Consistent styling and sizing
- Center-aligned using HTML:
```html
<div style="text-align:center">
    <img src="images/architecture.png" width="85%" />
</div>
```

### 5. Key Features
- Bullet point list of main capabilities
- 3-5 key features
- Focus on unique aspects of the implementation

### 6. Setup and Prerequisites

#### Prerequisites Subsection
- Python version requirement
- AWS account requirements
- Required AWS services and permissions
- External API requirements

#### Installation Subsection
```python
# installing pre-requisites
!pip install -r requirements.txt
```

#### Infrastructure Setup (if applicable)
- AWS resource deployment
- External service configuration
- API key setup

### 7. Imports and Configuration
```python
import os
import boto3
from strands import Agent, tool
from strands.models import BedrockModel
```

### 8. Core Implementation

#### For Agent-based Notebooks:
1. **Custom Tool Definitions**
   - Show decorator approach first
   - Include module-based approach example
   - Provide TOOL_SPEC example for complex tools

2. **System Prompt Definition**
   - Clear formatting with guidelines
   - Use structured tags when appropriate

3. **Model Configuration**
   ```python
   model = BedrockModel(
       model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
       # Optional configurations commented out
   )
   ```

4. **Agent Creation**
   ```python
   agent = Agent(
       model=model,
       system_prompt=system_prompt,
       tools=[tool1, tool2, tool3],
   )
   ```

### 9. Testing/Invocation
- Start with simple examples
- Progress to complex scenarios
- Include follow-up questions

### 10. Results Analysis
```python
# Analyze messages
agent.messages

# View metrics
results.metrics

# Tool usage analysis
for m in agent.messages:
    # Tool usage inspection code
```

### 11. Validation (optional)
- Verify actions were performed correctly
- Database checks
- Output validation

### 12. Cleanup (optional)
```python
# Optional cleanup
# !sh cleanup.sh
```

### 13. Conclusion
- Summary of accomplishments
- Next steps or modules
- Congratulatory message (for tutorials)

## Directory-Specific Guidelines

### 01-tutorials
- **Focus**: Educational content with detailed explanations
- **Structure**: Hierarchical numbering (F1-F8, M1-M3, D1-D2)
- **Style**: Step-by-step progression, multiple examples
- **Special Elements**:
  - Learning milestones
  - "Congratulations!" messages
  - CLI instructions for hands-on practice

### 02-samples
- **Focus**: Production-ready implementations
- **Structure**: Sequential numbering (01-, 02-, 03-) with descriptive names
- **Style**: Complete applications, real-world scenarios
- **Special Elements**:
  - Detailed feature tables
  - AWS service integration
  - Performance considerations

### 03-integrations
- **Focus**: External service connections
- **Structure**: Service/technology names without numbering
- **Style**: Technical setup and configuration
- **Special Elements**:
  - API key management
  - Service authentication patterns
  - External documentation links

### 05-agentic-rag
- **Focus**: Advanced RAG techniques
- **Structure**: Sequential numbering with technique descriptions
- **Style**: Research-oriented, performance-focused
- **Special Elements**:
  - 0-prerequisites notebooks
  - Evaluation metrics
  - Performance comparisons
  - Research methodology

## Code Style Guidelines

### Tool Definitions
```python
@tool
def tool_name(param1: str, param2: int) -> str:
    """
    Brief description of the tool.

    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2

    Returns:
        str: Description of return value
    """
    # Implementation
    pass
```

### System Prompts
```python
system_prompt = """You are a helpful assistant.

GUIDELINES:
- Guideline 1
- Guideline 2
- Guideline 3

<guidelines>
- Structured instruction 1
- Structured instruction 2
</guidelines>
"""
```

### Documentation Standards

#### Markdown Cells
- Use clear, hierarchical headers (##, ###, ####)
- Include explanatory text before each code section
- Keep explanations concise but informative
- Use bullet points for lists

#### Code Comments
- Minimal inline comments
- Use markdown cells for detailed explanations
- Only add comments for non-obvious logic

## Visual Assets Guidelines

### Architecture Diagrams
- Store in `images/` or `assets/` folder
- Use consistent color schemes
- Standard width: 85% for full diagrams, 65% for smaller diagrams
- Include alt text for accessibility

### Screenshots and Examples
- Use clear, high-resolution images
- Annotate when necessary
- Keep file sizes reasonable

## Testing and Validation Standards

### Example Invocations
```python
# Simple test
results = agent("Hello, how can you help me?")

# Complex scenario
results = agent("Create a reservation for tomorrow at 7pm")

# Follow-up
results = agent("Change it to 8pm instead")
```

### Results Analysis Pattern
```python
# Always show how to inspect results
print("Messages:", agent.messages)
print("Metrics:", results.metrics)

# Tool usage analysis
for m in agent.messages:
    for content in m["content"]:
        if "toolUse" in content:
            # Analyze tool usage
```

## File Naming Conventions

### Tutorials
- Format: `topic-name.ipynb`
- Example: `custom-tools-with-strands-agents.ipynb`

### Samples
- Format: `sample-name.ipynb`
- Example: `restaurant-assistant.ipynb`

### Integrations
- Format: `service-integration.ipynb`
- Example: `tavily-deep-research.ipynb`

### Prerequisites
- Format: `0-prerequisites.ipynb` or `0-prerequisites-topic.ipynb`
- Example: `0-prerequisites-structured-kb.ipynb`

## Common Patterns to Follow

### Package Installation
Always at the beginning, after prerequisites:
```python
!pip install -r requirements.txt
```

### Environment Variables
Use for sensitive data:
```python
os.environ["API_KEY"] = "your-key-here"
```

### AWS Service Configuration
```python
kb_id = smm_client.get_parameter(
    Name=f"{kb_name}-kb-id",
    WithDecryption=False
)
```

### Error Handling
Include try-except blocks for external service calls:
```python
try:
    response = external_service.call()
except Exception as e:
    return f"Error: {str(e)}"
```

## Quality Checklist

Before finalizing a notebook, ensure:

- [ ] Follows the standardized section structure
- [ ] Includes overview and feature table
- [ ] Has clear prerequisites and setup instructions
- [ ] Contains working examples with expected outputs
- [ ] Includes results analysis section
- [ ] Uses consistent code formatting
- [ ] Has appropriate markdown documentation
- [ ] Includes architecture diagram (if applicable)
- [ ] Tests run successfully
- [ ] No hardcoded credentials or sensitive data
- [ ] Cleanup section provided (if needed)

## Implementation Priority

1. **High Priority**: Update all notebooks in 01-tutorials and 02-samples
2. **Medium Priority**: Standardize 03-integrations notebooks
3. **Low Priority**: Update 05-agentic-rag and other specialized notebooks

## Maintenance Guidelines

1. Review notebooks quarterly for updates
2. Test all notebooks when updating dependencies
3. Update architecture diagrams when system changes
4. Keep prerequisites sections current
5. Archive deprecated notebooks with clear notices

## Conclusion

This standardization guide ensures consistency across all Jupyter notebooks in the project. By following these guidelines, we create a better learning experience for users and maintain a professional, cohesive codebase that's easy to navigate and understand.

For questions or suggestions about these standards, please open an issue in the project repository.