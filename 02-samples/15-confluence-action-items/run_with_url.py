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

def main():
    print("=" * 80)
    print("🔍 CONFLUENCE ACTION ITEMS ASSISTANT 🔍")
    print("=" * 80)
    
    # The URL provided by the user (view URL)
    confluence_url = "https://manojskrdev-1757832485500.atlassian.net/wiki/spaces/~7120208274e5fc76174bdbac8a10b291d7494e/pages/98309/2025-09-12+Meeting+notes"
    
    print(f"🔗 Processing Confluence URL: {confluence_url}")
    print()
    
    # Check if environment variables are set
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
        return
    
    print("✅ Confluence credentials found")
    print(f"🌐 Confluence URL: {confluence_url_env}")
    print(f"👤 Username: {confluence_username}")
    print()
    
    try:
        print("🔍 Analyzing Confluence page...")
        print("⏳ Reading page content and extracting action items...")
        print()
        
        # Extract page ID from the URL
        # URL format: .../pages/98309/2025-09-12+Meeting+notes
        if "/pages/" in confluence_url:
            parts = confluence_url.split("/pages/")[1]
            page_id = parts.split("/")[0]
            print(f"📄 Extracted page ID: {page_id}")
        else:
            print("❌ Could not extract page ID from URL")
            return
        
        # Process the request
        query = f"Please read the Confluence page with ID '{page_id}' and extract all action items. Use both the read_confluence_page and extract_action_items tools to provide a comprehensive analysis."
        
        response = action_items_agent(query)
        
        print("📊 Analysis Complete!")
        print("-" * 50)
        print(response)
        print("-" * 50)
        print()
        
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        print()
        print("🔧 Possible issues:")
        print("   - The page might be a draft or private")
        print("   - Invalid credentials")
        print("   - Network connectivity issues")
        print("   - The page ID might be incorrect")
    
    print(f"\n📈 Session metrics:\n{action_items_agent.event_loop_metrics}")

if __name__ == "__main__":
    main()
