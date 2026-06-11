#!/usr/bin/env python3
"""
Slack bot that answers AWS Partner Central questions via the MCP Server.

Uses Slack Bolt framework with Socket Mode for easy deployment.
Supports multi-turn conversations within Slack threads.

Prerequisites:
    export AWS_ACCESS_KEY_ID="your-access-key"
    export AWS_SECRET_ACCESS_KEY="your-secret-key"
    export SLACK_BOT_TOKEN="xoxb-your-bot-token"
    export SLACK_APP_TOKEN="xapp-your-app-token"

    pip install slack-bolt requests

Usage:
    python slack_agent.py
"""

import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from partner_central_client import PartnerCentralClient

# --- Configuration ---
app = App(token=os.environ["SLACK_BOT_TOKEN"])
pc_client = PartnerCentralClient()
pc_client.initialize()

# Track sessions per Slack thread for multi-turn conversations
thread_sessions = {}


@app.event("app_mention")
def handle_mention(event, say):
    """Respond to @mentions with Partner Central answers."""
    user = event["user"]
    text = event["text"]
    thread_ts = event.get("thread_ts", event["ts"])

    # Strip the bot mention from the message
    query = re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()

    if not query:
        say(
            text=(
                "Ask me anything about your AWS opportunities, "
                "funding programs, or pipeline! For example:\n"
                "• _List my open opportunities_\n"
                "• _Which deals are closing this month?_\n"
                "• _Am I eligible for MAP funding on O1234567890?_\n"
                "• _Generate a sales play for the Acme Corp deal_\n"
                "• _What are the top reasons we lost opportunities?_"
            ),
            thread_ts=thread_ts,
        )
        return

    # Use existing session for threaded conversations
    session_id = thread_sessions.get(thread_ts)

    say(text=":hourglass: Looking that up for you...", thread_ts=thread_ts)

    try:
        response = pc_client.send_message(
            text=query,
            catalog="AWS",
            session_id=session_id,
        )

        # Store session for follow-ups in the same thread
        if response["session_id"]:
            thread_sessions[thread_ts] = response["session_id"]

        # Send each response message
        if response["messages"]:
            for msg in response["messages"]:
                for chunk in _chunk_text(msg, 3900):
                    say(text=chunk, thread_ts=thread_ts)
        else:
            say(
                text=":warning: Got a response but no message content. "
                f"Status: {response['status']}",
                thread_ts=thread_ts,
            )

    except Exception as e:
        say(
            text=f":warning: Sorry, I hit an error: `{type(e).__name__}: {e}`",
            thread_ts=thread_ts,
        )


@app.event("message")
def handle_message(event, say):
    """Handle direct messages (DMs) to the bot."""
    # Only respond to DMs (channel type 'im'), not channel messages
    if event.get("channel_type") != "im":
        return

    # Ignore bot's own messages
    if event.get("bot_id"):
        return

    text = event.get("text", "").strip()
    thread_ts = event.get("thread_ts", event["ts"])

    if not text:
        return

    session_id = thread_sessions.get(thread_ts)

    try:
        response = pc_client.send_message(
            text=text,
            catalog="AWS",
            session_id=session_id,
        )

        if response["session_id"]:
            thread_sessions[thread_ts] = response["session_id"]

        if response["messages"]:
            for msg in response["messages"]:
                for chunk in _chunk_text(msg, 3900):
                    say(text=chunk, thread_ts=thread_ts)
        else:
            say(text=f":warning: No response. Status: {response['status']}", thread_ts=thread_ts)

    except Exception as e:
        say(
            text=f":warning: Error: `{type(e).__name__}: {e}`",
            thread_ts=thread_ts,
        )


def _chunk_text(text, max_len):
    """Split long messages into Slack-safe chunks."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        # Try to split at a newline near the limit
        if len(text) > max_len:
            split_at = text.rfind("\n", 0, max_len)
            if split_at == -1 or split_at < max_len // 2:
                split_at = max_len
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip("\n")
        else:
            chunks.append(text)
            break
    return chunks


if __name__ == "__main__":
    print("⚡ AWS Partner Central Slack Agent starting...")
    print("   Mention @bot in a channel or DM directly.")
    print("   Multi-turn conversations supported within threads.")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
