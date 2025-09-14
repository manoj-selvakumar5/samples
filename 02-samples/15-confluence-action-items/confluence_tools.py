import os
from typing import List, Dict, Any
from atlassian import Confluence
from dotenv import load_dotenv
from strands import tool

# Load environment variables from .env file
load_dotenv()

# Initialize constants
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_CLOUD = os.getenv("CONFLUENCE_CLOUD", "true").lower() == "true"

# Initialize Confluence client
confluence = Confluence(
    url=CONFLUENCE_URL,
    username=CONFLUENCE_USERNAME,
    password=CONFLUENCE_API_TOKEN,
    cloud=CONFLUENCE_CLOUD,
)


def extract_page_id_from_url(url: str) -> str:
    """Extract page ID from Confluence URL."""
    if "/pages/" in url:
        # Extract from URL like https://company.atlassian.net/wiki/spaces/SPACE/pages/12345/Page+Title
        parts = url.split("/pages/")
        if len(parts) > 1:
            page_id = parts[1].split("/")[0]
            return page_id
    raise ValueError(f"Could not extract page ID from URL: {url}")


@tool(
    name="read_confluence_page",
    description="Read content from a Confluence page by URL or page ID",
)
def read_confluence_page(page_identifier: str) -> str:
    """
    Read content from a Confluence page.

    Args:
        page_identifier (str): Either a Confluence page URL or page ID

    Returns:
        str: The page content as plain text
    """
    try:
        # Determine if input is URL or page ID
        if page_identifier.startswith("http"):
            page_id = extract_page_id_from_url(page_identifier)
        else:
            page_id = page_identifier

        # Get page content
        page = confluence.get_page_by_id(page_id, expand="body.storage")

        if not page:
            return f"Page with ID {page_id} not found."

        # Extract content from storage format
        content = page.get("body", {}).get("storage", {}).get("value", "")

        # Basic HTML to text conversion (remove common HTML tags)
        import re
        content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
        content = re.sub(r'&nbsp;', ' ', content)  # Replace &nbsp; with space
        content = re.sub(r'&amp;', '&', content)   # Replace &amp; with &
        content = re.sub(r'&lt;', '<', content)    # Replace &lt; with <
        content = re.sub(r'&gt;', '>', content)    # Replace &gt; with >
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Clean up excessive newlines

        title = page.get("title", "Untitled Page")

        return f"Title: {title}\n\n{content.strip()}"

    except Exception as e:
        return f"Error reading Confluence page: {str(e)}"


@tool(
    name="extract_action_items",
    description="Extract action items from text content using pattern matching",
)
def extract_action_items(content: str) -> List[Dict[str, Any]]:
    """
    Extract action items from text content using basic pattern matching.

    Args:
        content (str): The text content to analyze

    Returns:
        List[Dict[str, Any]]: List of action items with metadata
    """
    import re
    from datetime import datetime

    action_items = []
    lines = content.split('\n')

    # Patterns for different action item formats
    patterns = [
        r'(?i)(?:TODO|TO DO|Action|Task):\s*(.+)',
        r'(?i)(?:\[\s*\]|\[ \])\s*(.+)',  # Checkbox items
        r'(?i)@(\w+)\s+(.+)',  # @mentions with tasks
        r'(?i)(\w+)\s+(?:should|needs? to|must|will)\s+(.+)',  # Assignment patterns
    ]

    priority_keywords = {
        'high': ['urgent', 'critical', 'asap', 'high priority', 'important'],
        'medium': ['medium priority', 'normal'],
        'low': ['low priority', 'nice to have', 'optional']
    }

    date_pattern = r'(?i)(?:due|deadline|by)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})'

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                # Extract the action item text
                if pattern.startswith(r'(?i)@'):
                    assignee = match.group(1)
                    task = match.group(2).strip()
                else:
                    assignee = None
                    task = match.group(1).strip() if len(match.groups()) == 1 else match.group(2).strip()

                # Skip if task is too short or looks like a header
                if len(task.split()) < 2 or task.endswith(':'):
                    continue

                # Determine priority
                priority = 'medium'  # default
                task_lower = task.lower()
                for prio, keywords in priority_keywords.items():
                    if any(keyword in task_lower for keyword in keywords):
                        priority = prio
                        break

                # Look for assignee if not already found
                if not assignee:
                    assignee_match = re.search(r'(?i)(?:assigned to|owner|responsible):\s*(\w+(?:\s+\w+)?)', task)
                    if assignee_match:
                        assignee = assignee_match.group(1)

                # Look for due date
                due_date = None
                date_match = re.search(date_pattern, task)
                if date_match:
                    due_date = date_match.group(1)

                action_item = {
                    'task': task,
                    'assignee': assignee,
                    'priority': priority,
                    'due_date': due_date,
                    'line_number': i + 1,
                    'source_line': line
                }

                action_items.append(action_item)
                break  # Don't match multiple patterns for the same line

    return action_items