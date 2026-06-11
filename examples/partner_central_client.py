#!/usr/bin/env python3
"""
AWS Partner Central MCP Client Library

Handles SigV4 signing and JSON-RPC 2.0 communication with the
Partner Central Agent MCP Server.

Usage:
    from partner_central_client import PartnerCentralClient

    client = PartnerCentralClient()
    client.initialize()
    response = client.send_message("List all my open opportunities")
"""

import json
import datetime
import hashlib
import hmac
import os
import requests


class PartnerCentralClient:
    """Client for the AWS Partner Central MCP Server.

    Authenticates via AWS SigV4 and communicates using JSON-RPC 2.0.
    Credentials are read from environment variables:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_REGION (optional, defaults to us-east-1)
    """

    ENDPOINT = "https://partnercentral-agents-mcp.us-east-1.api.aws/mcp"
    SERVICE = "partnercentral-agents-mcp"
    REGION = "us-east-1"

    def __init__(self, access_key=None, secret_key=None, region=None):
        """Initialize the client.

        Args:
            access_key: AWS access key ID (defaults to AWS_ACCESS_KEY_ID env var)
            secret_key: AWS secret access key (defaults to AWS_SECRET_ACCESS_KEY env var)
            region: AWS region (defaults to AWS_REGION env var or us-east-1)
        """
        self.access_key = access_key or os.environ["AWS_ACCESS_KEY_ID"]
        self.secret_key = secret_key or os.environ["AWS_SECRET_ACCESS_KEY"]
        self.REGION = region or os.environ.get("AWS_REGION", "us-east-1")
        self._request_id = 0

    def _next_id(self):
        self._request_id += 1
        return self._request_id

    # --- SigV4 Signing ---

    def _sign(self, key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _get_signature_key(self, date_stamp):
        k_date = self._sign(
            ("AWS4" + self.secret_key).encode("utf-8"), date_stamp
        )
        k_region = self._sign(k_date, self.REGION)
        k_service = self._sign(k_region, self.SERVICE)
        k_signing = self._sign(k_service, "aws4_request")
        return k_signing

    def _sign_request(self, payload):
        from urllib.parse import urlparse

        t = datetime.datetime.now(datetime.UTC)
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        parsed = urlparse(self.ENDPOINT)
        host = parsed.hostname
        canonical_uri = parsed.path or "/"

        headers = {
            "content-type": "application/json",
            "host": host,
            "x-amz-date": amz_date,
        }

        signed_header_keys = sorted(headers.keys())
        canonical_headers = "".join(
            f"{k}:{headers[k]}\n" for k in signed_header_keys
        )
        signed_headers = ";".join(signed_header_keys)
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        canonical_request = "\n".join([
            "POST", canonical_uri, "",
            canonical_headers, signed_headers, payload_hash,
        ])

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.REGION}/{self.SERVICE}/aws4_request"
        string_to_sign = "\n".join([
            algorithm, amz_date, credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ])

        signing_key = self._get_signature_key(date_stamp)
        signature = hmac.new(
            signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        authorization = (
            f"{algorithm} Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        return {
            "content-type": "application/json",
            "x-amz-date": amz_date,
            "Authorization": authorization,
        }

    def _send(self, payload_dict):
        """Send a signed JSON-RPC request to the MCP endpoint."""
        payload = json.dumps(payload_dict)
        headers = self._sign_request(payload)
        response = requests.post(self.ENDPOINT, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()

    # --- Public API ---

    def initialize(self):
        """Initialize the MCP connection. Call once at startup.

        Returns:
            dict: Server info including protocol version and capabilities.
        """
        return self._send({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "partner-central-mcp-client",
                    "version": "1.0.0",
                },
            },
        })

    def list_tools(self):
        """List available MCP tools.

        Returns:
            dict: Available tools (sendMessage, getSession).
        """
        return self._send({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {},
        })

    def send_message(self, text, catalog="AWS", session_id=None):
        """Send a natural-language message to the Partner Central agent.

        Args:
            text: The message to send (natural language query).
            catalog: "AWS" for production, "Sandbox" for testing.
            session_id: Optional session ID for multi-turn conversations.

        Returns:
            dict with keys: session_id, status, messages (list of str).
        """
        arguments = {
            "content": [{"type": "text", "text": text}],
            "catalog": catalog,
        }
        if session_id:
            arguments["sessionId"] = session_id

        result = self._send({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": "sendMessage",
                "arguments": arguments,
            },
        })

        return self._parse_response(result)

    def get_session(self, session_id, catalog="AWS"):
        """Retrieve session history.

        Args:
            session_id: The session ID to retrieve.
            catalog: "AWS" for production, "Sandbox" for testing.

        Returns:
            dict with keys: session_id, status, messages (list of str).
        """
        result = self._send({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": "getSession",
                "arguments": {
                    "sessionId": session_id,
                    "catalog": catalog,
                },
            },
        })
        return self._parse_response(result)

    def _parse_response(self, result):
        """Extract the agent's text response from the JSON-RPC result."""
        content_list = result.get("result", {}).get("content", [])
        for block in content_list:
            if block.get("type") == "text":
                inner = json.loads(block["text"])
                return {
                    "session_id": inner.get("sessionId"),
                    "status": inner.get("status"),
                    "messages": [
                        c["content"]["text"]
                        for c in inner.get("content", [])
                        if c.get("type") == "ASSISTANT_RESPONSE"
                    ],
                }
        return {"session_id": None, "status": "error", "messages": []}
