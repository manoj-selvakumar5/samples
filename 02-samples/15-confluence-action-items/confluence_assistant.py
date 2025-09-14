#!/usr/bin/env python3

import logging
import json
import os
from strands import Agent
from strands.models import BedrockModel
from confluence_tools import read_confluence_page, extract_action_items

# Enable Strands debug log level
logging.getLogger("strands").setLevel(logging.DEBUG)

# Set logging format and stream logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# Initialize Bedrock model
model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
)

# System prompt for action items extraction
SYSTEM_PROMPT = """You are an expert at analyzing meeting notes and documentation to identify action items.

Your task is to:
1. Read Confluence page content when provided with a URL or page ID
2. Identify all action items, tasks, TODOs, and assignments from the content
3. Extract relevant details like assignees, due dates, and priorities
4. Present the findings in a clear, structured format

When analyzing content, look for:
- TODO items and action lists
- Tasks assigned to specific people (@mentions, "assigned to", "owner")
- Items with checkboxes or bullet points indicating tasks
- Due dates and deadlines
- Priority indicators (urgent, high, medium, low)
- Follow-up items and next steps

Always provide a comprehensive summary of all action items found, even if some details are missing."""

# Create the Confluence action items agent
action_items_agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        read_confluence_page,
        extract_action_items,
    ],
)


def format_action_items(action_items_response: str) -> str:
    """Format the action items response for better readability."""
    if not action_items_response:
        return "No action items found."

    # Try to parse as JSON if it looks like structured data
    try:
        if action_items_response.startswith('['):
            items = json.loads(action_items_response)
            formatted = "\n📋 Action Items Found:\n" + "="*50 + "\n\n"

            for i, item in enumerate(items, 1):
                formatted += f"{i}. "

                # Priority indicator
                priority = item.get('priority', 'medium').upper()
                priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "🟡")
                formatted += f"[{priority_emoji} {priority}] "

                # Task description
                formatted += f"{item.get('task', 'No description')}"

                # Assignee
                if item.get('assignee'):
                    formatted += f" - 👤 {item['assignee']}"

                # Due date
                if item.get('due_date'):
                    formatted += f" - 📅 Due: {item['due_date']}"

                formatted += "\n"

                # Source line reference
                if item.get('line_number'):
                    formatted += f"   📍 Line {item['line_number']}: {item.get('source_line', '')}\n"

                formatted += "\n"

            return formatted
    except (json.JSONDecodeError, TypeError):
        pass

    # Return original response if not JSON
    return action_items_response


def extract_page_id_from_url(confluence_url: str) -> str:
    """Extract page ID from Confluence URL."""
    if "/pages/" in confluence_url:
        parts = confluence_url.split("/pages/")[1]
        return parts.split("/")[0]
    return confluence_url  # Return as-is if it's already a page ID


def check_credentials() -> bool:
    """Check if Confluence credentials are properly configured."""
    confluence_url_env = os.getenv("CONFLUENCE_URL")
    confluence_username = os.getenv("CONFLUENCE_USERNAME")
    confluence_token = os.getenv("CONFLUENCE_API_TOKEN")

    if not all([confluence_url_env, confluence_username, confluence_token]):
        print("❌ Missing Confluence credentials!")
        print("📝 Please set the following environment variables:")
        print("   - CONFLUENCE_URL (e.g., https://yourcompany.atlassian.net)")
        print("   - CONFLUENCE_USERNAME (your email)")
        print("   - CONFLUENCE_API_TOKEN (from https://id.atlassian.com/manage-profile/security/api-tokens)")
        print()
        print("💡 You can create a .env file with these values")
        return False

    print("✅ Confluence credentials found")
    print(f"🌐 Confluence URL: {confluence_url_env}")
    print(f"👤 Username: {confluence_username}")
    print()
    return True


if __name__ == "__main__":
    print("=" * 80)
    print("🔍 CONFLUENCE ACTION ITEMS ASSISTANT 🔍")
    print("=" * 80)
    print("✨ I can analyze Confluence pages and extract action items!")
    print("📄 Supported inputs:")
    print("   • Confluence page URL (e.g., https://company.atlassian.net/wiki/spaces/...)")
    print("   • Page ID (e.g., 123456789)")
    print()
    print("🤖 I'll use AI to identify tasks, assignments, and deadlines")
    print("🚪 Type 'exit' to quit anytime")
    print("=" * 80)
    print()

    # Check credentials first
    if not check_credentials():
        exit(1)

    try:
        print("🔄 Initializing Confluence Action Items Assistant...")
        print("✅ Agent ready!")
        print()
    except Exception as e:
        print(f"❌ Error initializing agent: {str(e)}")
        exit(1)

    while True:
        try:
            user_input = input("🔗 Enter Confluence page URL or page ID (or paste URL): ").strip()

            if not user_input:
                print("💭 Please provide a Confluence page URL or ID, or type 'exit' to quit")
                continue

            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print()
                print("=" * 50)
                print("👋 Thank you for using Confluence Action Items Assistant!")
                print("📋 Hope you found all your action items!")
                print("=" * 50)
                break

            print(f"\n🔍 Analyzing Confluence page: {user_input}")

            # Extract page ID if it's a URL
            page_identifier = extract_page_id_from_url(user_input)
            if page_identifier != user_input:
                print(f"📄 Extracted page ID: {page_identifier}")

            print("⏳ Reading page content and extracting action items...")
            print()

            # Process the request
            query = f"Please read the Confluence page with ID '{page_identifier}' and extract all action items. Use both the read_confluence_page and extract_action_items tools to provide a comprehensive analysis."

            response = action_items_agent(query)

            print("📊 Analysis Complete!")
            print("-" * 50)
            print(format_action_items(response))
            print("-" * 50)
            print()

        except KeyboardInterrupt:
            print("\n")
            print("=" * 50)
            print("👋 Confluence Action Items Assistant interrupted!")
            print("📋 See you next time!")
            print("=" * 50)
            break
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            print("🔧 Possible issues:")
            print("   - The page might be a draft or private")
            print("   - Invalid credentials")
            print("   - Network connectivity issues")
            print("   - The page ID might be incorrect")
            print("🔧 Please try again or type 'exit' to quit")
            print()

    print(f"\n📈 Session metrics:\n{action_items_agent.event_loop_metrics}")