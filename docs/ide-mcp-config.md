# MCP Server Configuration Examples

## Claude Code

Add to `.mcp.json` (project-level) or `~/.claude.json` (global):

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

Or via CLI:

```bash
claude mcp add-json partner-central \
  '{"type":"stdio","command":"node","args":["./aws-partner-central-mcp/server/index.js"],"env":{"AWS_SSO_START_URL":"https://your-org.awsapps.com/start","PARTNER_CENTRAL_DEFAULT_CATALOG":"AWS"}}'
```

## Kiro

Add to `.kiro/settings/mcp.json` (workspace) or `~/.kiro/settings/mcp.json` (global):

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

## Claude Desktop

Download the `.mcpb` bundle from [customd/aws-partner-central-mcp Releases](https://github.com/customd/aws-partner-central-mcp/releases) and drag it into **Settings → Extensions**. Enter your SSO Start URL when prompted.

## Why a Local Proxy?

The Partner Central MCP Server (`partnercentral-agents-mcp.us-east-1.api.aws/mcp`) requires AWS SigV4 request signing on every request (including signing the request body). Neither Claude Code nor Kiro supports SigV4 natively for remote HTTP connections.

The [customd/aws-partner-central-mcp](https://github.com/customd/aws-partner-central-mcp) project provides a local stdio MCP server that:
1. Receives standard MCP requests from your IDE
2. Signs them with SigV4 using your AWS credentials (via SSO)
3. Forwards them to the Partner Central endpoint
4. Returns responses back to your IDE

### Setup

```bash
git clone https://github.com/customd/aws-partner-central-mcp.git
cd aws-partner-central-mcp
npm install
npm run build
```

Then reference `server/index.js` in the configurations above.
