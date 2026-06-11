#!/usr/bin/env python3
"""
Interactive CLI chat with the AWS Partner Central Agent.

Provides a REPL interface for conversing with the Partner Central agent,
maintaining session context across messages.

Prerequisites:
    export AWS_ACCESS_KEY_ID="your-access-key"
    export AWS_SECRET_ACCESS_KEY="your-secret-key"

Usage:
    python interactive_chat.py [--sandbox]
"""

import sys
from partner_central_client import PartnerCentralClient


def main():
    catalog = "Sandbox" if "--sandbox" in sys.argv else "AWS"

    print("=" * 60)
    print("AWS Partner Central - Interactive Chat")
    print("=" * 60)
    print(f"Catalog: {catalog}")
    print("Type 'quit' or 'exit' to end the session.")
    print("Type 'new' to start a fresh session.")
    print("-" * 60)

    try:
        client = PartnerCentralClient()
    except KeyError as e:
        print(f"\nERROR: Missing environment variable: {e}")
        print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY before running.")
        sys.exit(1)

    client.initialize()
    session_id = None

    while True:
        try:
            query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not query:
            continue

        if query.lower() in ("quit", "exit"):
            print("\nGoodbye!")
            break

        if query.lower() == "new":
            session_id = None
            print("  [Started new session]")
            continue

        try:
            response = client.send_message(
                text=query,
                catalog=catalog,
                session_id=session_id,
            )

            session_id = response["session_id"]

            if response["messages"]:
                for msg in response["messages"]:
                    print(f"\nAgent: {msg}")
            else:
                print(f"\n  [No response. Status: {response['status']}]")

        except Exception as e:
            print(f"\n  [Error: {type(e).__name__}: {e}]")

    if session_id:
        print(f"\nSession ID (for resuming): {session_id}")


if __name__ == "__main__":
    main()
