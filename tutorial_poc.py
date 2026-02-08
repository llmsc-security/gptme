#!/usr/bin/env python3
"""
Tutorial PoC for testing gptme-server HTTP endpoints.

This script demonstrates how to use the gptme-server REST API.
It tests the following endpoints:
- GET /api - Check server health
- GET /api/conversations - List conversations
- POST /api/conversations/<id>/generate - Generate AI response

Usage:
    # Start the server first (in another terminal):
    # docker run -p 11130:8000 -e GPTME_DISABLE_AUTH=true gptme-server:latest

    # Then run this script:
    python tutorial_poc.py
"""

import requests
import json
import time
from typing import Optional


class GPTMeAPIClient:
    """Client for interacting with gptme-server REST API."""

    def __init__(self, base_url: str = "http://localhost:11130"):
        """Initialize the API client.

        Args:
            base_url: The base URL of the gptme-server.
        """
        self.base_url = base_url.rstrip("/")

    def get_api_root(self) -> dict:
        """Test GET /api endpoint.

        Returns:
            Response from the API root endpoint.
        """
        response = requests.get(f"{self.base_url}/api")
        response.raise_for_status()
        return response.json()

    def get_conversations(self, limit: int = 100) -> list:
        """Test GET /api/conversations endpoint.

        Args:
            limit: Maximum number of conversations to return.

        Returns:
            List of conversations.
        """
        response = requests.get(
            f"{self.base_url}/api/conversations",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def create_conversation(
        self,
        logfile: str,
        messages: Optional[list] = None,
        config: Optional[dict] = None
    ) -> dict:
        """Create a new conversation.

        Args:
            logfile: Name of the conversation file.
            messages: Optional list of initial messages.
            config: Optional configuration dict.

        Returns:
            Status response from the server.
        """
        payload = {"logfile": logfile}
        if messages:
            payload["messages"] = messages
        if config:
            payload["config"] = config

        response = requests.put(
            f"{self.base_url}/api/conversations/{logfile}",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_conversation(self, logfile: str) -> dict:
        """Get a specific conversation.

        Args:
            logfile: Name of the conversation file.

        Returns:
            Conversation details including messages.
        """
        response = requests.get(f"{self.base_url}/api/conversations/{logfile}")
        response.raise_for_status()
        return response.json()

    def add_message(
        self,
        logfile: str,
        role: str,
        content: str,
        branch: str = "main"
    ) -> dict:
        """Add a message to a conversation.

        Args:
            logfile: Name of the conversation file.
            role: Message role ('user', 'assistant', 'system').
            content: Message content.
            branch: Branch name (default: 'main').

        Returns:
            Status response from the server.
        """
        payload = {
            "role": role,
            "content": content,
            "branch": branch
        }

        response = requests.post(
            f"{self.base_url}/api/conversations/{logfile}",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def generate_response(
        self,
        logfile: str,
        model: Optional[str] = None,
        stream: bool = False
    ) -> dict:
        """Generate an AI response in a conversation.

        Args:
            logfile: Name of the conversation file.
            model: Model to use (optional, uses server default if not specified).
            stream: Whether to use streaming (default: False).

        Returns:
            Generated response(s) from the model.
        """
        payload = {"model": model, "stream": stream}

        response = requests.post(
            f"{self.base_url}/api/conversations/{logfile}/generate",
            json=payload,
            timeout=120  # Extended timeout for model generation
        )
        response.raise_for_status()
        return response.json()

    def generate_response_stream(
        self,
        logfile: str,
        model: Optional[str] = None
    ):
        """Generate an AI response with streaming.

        Args:
            logfile: Name of the conversation file.
            model: Model to use (optional).

        Yields:
            Chunks of the response as they arrive.
        """
        payload = {"model": model, "stream": True}

        response = requests.post(
            f"{self.base_url}/api/conversations/{logfile}/generate",
            json=payload,
            stream=True,
            timeout=120
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data = line_str[6:]  # Remove "data: " prefix
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        print(f"Failed to parse: {data}")


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def main():
    """Run the tutorial PoC demonstrating gptme-server API usage."""
    print_section("GPTMe Server API Tutorial PoC")
    print(f"Connecting to server at: http://localhost:11130")
    print("\nNote: This script requires the gptme-server to be running.")
    print("Start it with: docker run -p 11130:8000 gptme-server:latest")

    # Initialize the client
    client = GPTMeAPIClient("http://localhost:11130")

    try:
        # Test 1: API Root
        print_section("Test 1: GET /api (Server Health)")
        print("Checking if the server is running...")
        try:
            api_root = client.get_api_root()
            print(f"Server response: {api_root.get('message', 'No message')}")
            print("SUCCESS: Server is running!")
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to the server.")
            print("\nTo start the server in Docker:")
            print("  docker run -p 11130:8000 -e GPTME_DISABLE_AUTH=true gptme-server:latest")
            return

        # Test 2: List Conversations
        print_section("Test 2: GET /api/conversations (List Conversations)")
        conversations = client.get_conversations(limit=5)
        print(f"Found {len(conversations)} conversation(s):")
        for conv in conversations:
            print(f"  - {conv}")

        # Test 3: Create a new conversation
        print_section("Test 3: PUT /api/conversations/<id> (Create Conversation)")
        conversation_id = "tutorial-conversation"
        print(f"Creating conversation: {conversation_id}")
        client.create_conversation(
            logfile=conversation_id,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Hello, how are you?"}
            ]
        )
        print(f"SUCCESS: Created conversation '{conversation_id}'")

        # Test 4: Get conversation details
        print_section("Test 4: GET /api/conversations/<id> (Get Conversation)")
        conv_details = client.get_conversation(conversation_id)
        print(f"Conversation workspace: {conv_details.get('workspace', 'N/A')}")
        print(f"Number of messages: {len(conv_details.get('log', []))}")
        print("Messages:")
        for msg in conv_details.get('log', []):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:100]  # Truncate for display
            print(f"  [{role}] {content}{'...' if len(content) > 100 else ''}")

        # Test 5: Generate response (non-streaming)
        print_section("Test 5: POST /api/conversations/<id>/generate (Generate Response)")
        print("Generating AI response...")
        try:
            response = client.generate_response(conversation_id)
            print("Generated response(s):")
            for msg in response:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                print(f"  [{role}] {content[:200]}{'...' if len(content) > 200 else ''}")
            print("SUCCESS: Response generated!")
        except Exception as e:
            print(f"Note: Generation may require API keys or model configuration.")
            print(f"Error: {e}")

        # Test 6: Add message and generate (streaming)
        print_section("Test 6: Streaming Generation Demo")
        print("Adding a new user message...")
        client.add_message(
            logfile=conversation_id,
            role="user",
            content="Write a simple Python function to calculate factorial."
        )
        print("Starting streaming generation...")
        try:
            print("Response chunks:")
            for chunk in client.generate_response_stream(conversation_id):
                role = chunk.get('role', 'unknown')
                content = chunk.get('content', '')
                stored = chunk.get('stored', False)
                print(f"  [{role}, stored={stored}] {content}")
            print("SUCCESS: Streaming completed!")
        except Exception as e:
            print(f"Note: Streaming generation may require API keys or model configuration.")
            print(f"Error: {e}")

        print_section("Tutorial Complete!")
        print("\nAPI Endpoints demonstrated:")
        print("  1. GET /api - Server health check")
        print("  2. GET /api/conversations - List conversations")
        print("  3. PUT /api/conversations/<id> - Create conversation")
        print("  4. GET /api/conversations/<id> - Get conversation details")
        print("  5. POST /api/conversations/<id>/generate - Generate response")
        print("  6. Streaming generation with POST /api/conversations/<id>/generate")
        print("\nNext steps:")
        print("  - Set GPTME_SERVER_TOKEN to enable authentication")
        print("  - Set MODEL environment variable to configure the LLM")
        print("  - Visit http://localhost:11130 for the web UI")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
