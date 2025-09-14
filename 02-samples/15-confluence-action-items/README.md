# Confluence Action Items Agent

This Strands Agent reads Confluence pages and extracts action items using Amazon Bedrock's Claude Sonnet model. The agent intelligently identifies tasks, TODOs, assignments, and other action items from meeting notes and documentation.

## Features

- ✅ Reads Confluence pages via REST API
- ✅ Extracts action items using AI-powered analysis
- ✅ Identifies assignees, due dates, and priorities
- ✅ Provides structured output of all action items

## Prerequisites

- Python 3.9+
- AWS credentials configured for Bedrock
- Confluence API token

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Confluence API access**:
   - For Confluence Cloud: Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens
   - Copy `.env.example` to `.env` and fill in your credentials:
     ```
     CONFLUENCE_URL=https://yourcompany.atlassian.net
     CONFLUENCE_USERNAME=your.email@company.com
     CONFLUENCE_API_TOKEN=your_api_token_here
     CONFLUENCE_CLOUD=true
     ```

3. **Configure AWS Bedrock**:
   - Ensure your AWS credentials are configured
   - Verify access to Claude Sonnet model in your region

## Usage

Run the agent:
```bash
python confluence_assistant.py
```

Provide a Confluence page URL or page ID when prompted. The agent will:
1. Connect to Confluence and fetch the page content
2. Analyze the content using Bedrock's Claude Sonnet model
3. Extract and display all identified action items

## Example Output

```
Action Items Found:
1. [High Priority] Update project timeline - Assigned to: John Doe - Due: 2024-01-15
2. [Medium Priority] Review security documentation - Assigned to: Jane Smith
3. [Low Priority] Schedule follow-up meeting - No assignee specified
```

## Supported Action Item Patterns

The agent recognizes various patterns including:
- TODO items
- Action: statements
- @mentions with tasks
- Checkbox items
- Due date references
- Priority indicators