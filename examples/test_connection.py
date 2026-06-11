#!/usr/bin/env python3
"""
Test connectivity to the AWS Partner Central MCP Server.

Performs three tests:
1. Initialize - establishes MCP protocol connection
2. List Tools - discovers available tools
3. Send Message (Sandbox) - sends a test message to the sandbox environment

Prerequisites:
    export AWS_ACCESS_KEY_ID="your-access-key"
    export AWS_SECRET_ACCESS_KEY="your-secret-key"

Usage:
    python test_connection.py
"""

import json
import sys
from partner_central_client import PartnerCentralClient


def main():
    print("=" * 60)
    print("AWS Partner Central MCP Server - Connection Test")
    print("=" * 60)

    try:
        client = PartnerCentralClient()
    except KeyError as e:
        print(f"\nERROR: Missing environment variable: {e}")
        print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY before running.")
        sys.exit(1)

    # Test 1: Initialize
    print("\n[1/3] Initializing MCP connection...")
    try:
        init_result = client.initialize()
        server_info = init_result.get("result", {}).get("serverInfo", {})
        print(f"  ✅ Connected to: {server_info.get('name')} v{server_info.get('version')}")
        protocol = init_result.get("result", {}).get("protocolVersion")
        print(f"  Protocol: {protocol}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        sys.exit(1)

    # Test 2: List Tools
    print("\n[2/3] Listing available tools...")
    try:
        tools_result = client.list_tools()
        tools = tools_result.get("result", {}).get("tools", [])
        print(f"  ✅ {len(tools)} tools available:")
        for tool in tools:
            print(f"     - {tool['name']}: {tool['description'][:80]}...")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        sys.exit(1)

    # Test 3: Send a test message to Sandbox
    print("\n[3/3] Sending test message (Sandbox catalog)...")
    try:
        response = client.send_message(
            "Hello, what can you help me with?",
            catalog="Sandbox",
        )
        print(f"  ✅ Status: {response['status']}")
        print(f"  Session ID: {response['session_id']}")
        if response["messages"]:
            preview = response["messages"][-1][:150]
            print(f"  Response preview: {preview}...")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED - Connection is working correctly")
    print("=" * 60)


if __name__ == "__main__":
    main()
