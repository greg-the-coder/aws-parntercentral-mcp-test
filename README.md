# AWS Partner Central MCP Server — Examples & Guide

Build agents and bots that talk to your AWS co-sell pipeline using the Partner Central MCP Server. This repository contains a tested Python client library, example integrations (Slack bot, interactive CLI), and configuration guides for Claude Code, Kiro, and Claude Desktop.

**All sample queries in this guide have been validated against a live Partner Central account.**

---

## Repository Structure

```
.
├── README.md                           # This file — full how-to guide
├── requirements.txt                    # Python dependencies
├── examples/
│   ├── partner_central_client.py       # Core MCP client library (SigV4 + JSON-RPC)
│   ├── test_connection.py              # Connection validation script
│   ├── test_sample_queries.py          # Validates all sample queries from this guide
│   ├── slack_agent.py                  # Slack bot integration
│   └── interactive_chat.py            # Interactive CLI chat
└── docs/
    ├── iam-policies.md                 # IAM policy reference
    └── ide-mcp-config.md              # Claude Code / Kiro / Claude Desktop config
```

---

## Quick Start

```bash
# Clone this repo
git clone https://github.com/greg-the-coder/aws-parntercentral-mcp-test.git
cd aws-parntercentral-mcp-test

# Install dependencies
pip install -r requirements.txt

# Set credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Verify connectivity
cd examples
python test_connection.py
```

---

## Architecture

```
┌──────────────┐       ┌──────────────────┐       ┌─────────────────────────────────────────────┐
│  Slack User  │──────▶│  Your Slack App   │──────▶│  Agent Service (Python/Node)                │
│  "List my    │       │  (Event handler)  │       │    • Receives message                       │
│   open opps" │       │                   │       │    • Signs request with SigV4               │
└──────────────┘       └──────────────────┘       │    • Calls Partner Central MCP endpoint     │
                                                   │    • Returns response to Slack              │
                                                   └────────────────────┬────────────────────────┘
                                                                        │ HTTPS + SigV4
                                                                        ▼
                                                   ┌─────────────────────────────────────────────┐
                                                   │  AWS Partner Central MCP Server              │
                                                   │  partnercentral-agents-mcp.us-east-1.api.aws │
                                                   └─────────────────────────────────────────────┘
```

---

## Prerequisites

- An active AWS Partner Central account (migrated to AWS console)
- An AWS IAM identity with the required permissions (see below)
- AWS credentials configured (IAM user keys, SSO, or IAM role)
- Python 3.9+
- A Slack workspace with permission to create apps (for the Slack integration)

---

## IAM Permissions

### Read-Only Policy: `coder-partner-mcp-readonly`

We use the `coder-partner-mcp-readonly` IAM policy (`arn:aws:iam::<your-account-id>:policy/coder-partner-mcp-readonly`). This policy is sufficient for all queries demonstrated in this guide.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "partnercentral:UseSession",
                "partnercentral:List*",
                "partnercentral:Get*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "aws-marketplace:DescribeEntity",
                "aws-marketplace:DescribeAgreement",
                "aws-marketplace:SearchAgreements",
                "aws-marketplace:ListEntities"
            ],
            "Resource": "*"
        }
    ]
}
```

Attach to a user or role:

```bash
aws iam attach-user-policy \
    --user-name <your-iam-user> \
    --policy-arn arn:aws:iam::<your-account-id>:policy/coder-partner-mcp-readonly
```

For write operations (opportunity creation, funding applications), see [docs/iam-policies.md](docs/iam-policies.md).

---

## MCP Protocol Reference

| Property | Value |
|----------|-------|
| Endpoint | `https://partnercentral-agents-mcp.us-east-1.api.aws/mcp` |
| Protocol | JSON-RPC 2.0 over HTTPS |
| Authentication | AWS SigV4 |
| SigV4 Service Name | `partnercentral-agents-mcp` |
| Region | `us-east-1` (only) |
| TLS | 1.2+ required |
| Rate Limit | `sendMessage`: 2/min sustained, burst 10 |
| Session Duration | 48 hours |

### Available Tools

| Tool | Purpose |
|------|---------|
| `sendMessage` | Send a natural-language message to the agent (primary tool) |
| `getSession` | Retrieve the state/history of an existing session |

### Catalog Environments

| Catalog | Use |
|---------|-----|
| `"AWS"` | Production — live partner data |
| `"Sandbox"` | Isolated testing — no impact on production |

---

## Using the Python Client

The `examples/partner_central_client.py` library handles SigV4 signing and JSON-RPC communication:

```python
from partner_central_client import PartnerCentralClient

# Credentials from environment variables
client = PartnerCentralClient()
client.initialize()

# Ask about open opportunities
response = client.send_message("List all my open opportunities")
print(f"Session: {response['session_id']}")
for msg in response["messages"]:
    print(msg)

# Follow up in the same session (multi-turn)
response = client.send_message(
    "Which of those are closing this month?",
    session_id=response["session_id"],
)
for msg in response["messages"]:
    print(msg)
```

---

## Validated Sample Queries

All queries below have been tested and confirmed working against the production MCP server:

| Category | Query | Status |
|----------|-------|--------|
| **Pipeline overview** | "List all my open opportunities" | ✅ |
| | "How many opportunities are closing next month?" | ✅ |
| | "Which opportunities need my attention this week?" | ✅ |
| **Opportunity detail** | "Give me a summary of opportunity O14310233" | ✅ |
| | "What's the current stage and expected revenue for the Coder deal?" | ✅ |
| **Sales strategy** | "Generate a sales play for opportunity O14310233" | ✅ |
| | "What are the next steps to advance opportunity O14310233?" | ✅ |
| **Funding programs** | "Am I eligible for MAP funding on opportunity O14310233?" | ✅ |
| | "What funding programs are available for a POC?" | ✅ |
| **Customer insights** | "Create a customer profile for Coder" | ✅ |
| | "Which of our solutions best match opportunity O14310233?" | ✅ |
| **Loss analysis** | "What are the top reasons we lost opportunities in the last 6 months?" | ✅ |

Run the validation suite yourself:

```bash
cd examples
python test_sample_queries.py          # Production
python test_sample_queries.py --sandbox  # Sandbox (no live data)
```

---

## Slack Bot Integration

### Create the Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App**
2. Choose **From scratch**, name it (e.g., "AWS Pipeline Bot")
3. Under **OAuth & Permissions**, add scopes:
   - `app_mentions:read`
   - `chat:write`
   - `channels:history`
   - `im:history` (for DMs)
4. Under **Event Subscriptions**, subscribe to `app_mention` and `message.im` events
5. Under **Socket Mode**, enable it and generate an App-Level Token
6. Install the app to your workspace

### Run the Bot

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_APP_TOKEN="xapp-your-app-token"

cd examples
python slack_agent.py
```

### Features

- **@mention in channels** — mention the bot with a question
- **Direct messages** — DM the bot for private queries
- **Multi-turn conversations** — threaded replies maintain session context
- **Automatic chunking** — long responses are split into Slack-safe messages

### Example Slack Interactions

```
@pipeline-bot List my open opportunities closing in July
@pipeline-bot Am I eligible for MAP funding on O14310233?
@pipeline-bot Generate a sales play for the Netflix deal
@pipeline-bot What are the top reasons we lost deals last quarter?
```

---

## Interactive CLI

For quick ad-hoc queries:

```bash
cd examples
python interactive_chat.py             # Production
python interactive_chat.py --sandbox   # Sandbox
```

```
You: List my open opportunities
Agent: You have 235 active opportunities across all stages...

You: Which are in Business Validation?
Agent: Here are your opportunities in Business Validation stage...

You: quit
```

---

## IDE Integration (Claude Code / Kiro)

The Partner Central MCP Server requires SigV4 signing, which Claude Code and Kiro don't support natively. Use a **local stdio proxy** — see [docs/ide-mcp-config.md](docs/ide-mcp-config.md) for complete setup instructions.

### Quick Config (Claude Code)

```json
{
  "mcpServers": {
    "partner-central": {
      "type": "stdio",
      "command": "node",
      "args": ["./aws-partner-central-mcp/server/index.js"],
      "env": {
        "AWS_SSO_START_URL": "https://your-org.awsapps.com/start",
        "PARTNER_CENTRAL_DEFAULT_CATALOG": "AWS"
      }
    }
  }
}
```

### Quick Config (Kiro)

```json
{
  "mcpServers": {
    "partner-central": {
      "command": "node",
      "args": ["./aws-partner-central-mcp/server/index.js"],
      "env": {
        "AWS_SSO_START_URL": "https://your-org.awsapps.com/start",
        "PARTNER_CENTRAL_DEFAULT_CATALOG": "AWS"
      }
    }
  }
}
```

---

## Production Considerations

### Security

- **Never hardcode credentials.** Use environment variables, AWS Secrets Manager, or IAM roles.
- **Use the Sandbox catalog** (`"Sandbox"`) for all development and testing.
- **Apply least-privilege IAM policies.** Use `coder-partner-mcp-readonly` for reporting bots and Slack agents; only grant write permissions to agents that explicitly need to create/update opportunities.
- **Do not pass credentials through MCP tool parameters.** Authentication is handled at the transport layer via SigV4.

### Rate Limits

| Operation | Sustained Rate | Burst |
|-----------|---------------|-------|
| `sendMessage` | 2 requests/min | 10 |
| All other operations | 10 requests/min | 20 |

Implement exponential backoff with jitter. For a Slackbot serving a team, consider a request queue.

### Session Management

- Sessions expire after **48 hours** (absolute, not inactivity-based).
- Sessions are **catalog-scoped** — a Sandbox session cannot be reused with the AWS catalog.
- Store session IDs per Slack thread or per user for multi-turn conversations.

### Error Handling

| Code | Name | Action |
|------|------|--------|
| -32001 | AUTHENTICATION_FAILURE | Refresh/rotate credentials |
| -31004 | TOOL_PERMISSION_DENIED | Check IAM policy |
| -32002 | ACCESS_DENIED | Verify account enrollment |
| -32004 | LIMIT_EXCEEDED | Backoff and retry |
| -30001 | RESOURCE_NOT_FOUND | Session expired or invalid ID |
| -32600 | INVALID_REQUEST | Fix request format |
| -32603 | INTERNAL_ERROR | Retry |

---

## Advanced: Streaming Responses (SSE)

For a more responsive user experience, enable streaming:

```python
arguments = {
    "content": [{"type": "text", "text": "List my open opportunities"}],
    "catalog": "AWS",
    "stream": True,  # Enable Server-Sent Events
}
```

SSE event types:

| Event | Meaning |
|-------|---------|
| `stream_start` | Connection established |
| `assistant-response.start` | Agent began generating |
| `assistant-response.delta` | Incremental text chunk |
| `assistant-response.completed` | Response finished |
| `server-tool-use` | Agent invoking an internal tool |
| `server-tool-response` | Tool result |
| `tool_approval_request` | Write operation needs human approval |
| `stream_end` | Stream closing |
| `done` | Final event |

---

## Advanced: Human-in-the-Loop for Write Operations

When the agent needs to perform a write (create opportunity, submit funding request), it returns a `tool_approval_request` instead of executing immediately. Your agent should:

1. Present the proposed change to the user (e.g., in Slack with action buttons).
2. Collect their approval/rejection.
3. Send the decision back using a `tool_approval_response` content block:

```python
arguments = {
    "content": [{
        "type": "tool_approval_response",
        "toolUseId": "<the-tool-use-id-from-the-request>",
        "decision": "approve",  # or "reject" or "override"
        "message": "Looks good, proceed."
    }],
    "catalog": "AWS",
    "sessionId": session_id,
}
```

---

## JSON-RPC Quick Reference

### Initialize Connection
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {
            "name": "your-app-name",
            "version": "1.0.0",
            "integrator": "Your Company",
            "sourceProduct": "Your App"
        }
    }
}
```

### Send a Message
```json
{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "sendMessage",
        "arguments": {
            "content": [{"type": "text", "text": "List my open opportunities"}],
            "catalog": "AWS",
            "sessionId": "session-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        },
        "_meta": {
            "integrator": "Your Company",
            "sourceProduct": "Your App"
        }
    }
}
```

### List Available Tools
```json
{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/list",
    "params": {}
}
```

---

## Resources

- [AWS Partner Central MCP Getting Started](https://docs.aws.amazon.com/partner-central/latest/APIReference/mcp-getting-started.html)
- [Configuration Reference](https://docs.aws.amazon.com/partner-central/latest/APIReference/mcp-configuration-reference.html)
- [Tools Reference](https://docs.aws.amazon.com/partner-central/latest/APIReference/mcp-tools-reference.html)
- [Open-source Claude Desktop extension (SigV4 proxy)](https://github.com/customd/aws-partner-central-mcp)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Slack Bolt for Python](https://slack.dev/bolt-python/)

---

## License

See [LICENSE](LICENSE).
