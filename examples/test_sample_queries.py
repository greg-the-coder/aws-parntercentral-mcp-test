#!/usr/bin/env python3
"""
Test all sample queries against the AWS Partner Central MCP Server.

Validates the queries documented in the README by running them against
the production (AWS) catalog and confirming successful responses.

Prerequisites:
    export AWS_ACCESS_KEY_ID="your-access-key"
    export AWS_SECRET_ACCESS_KEY="your-secret-key"

Usage:
    python test_sample_queries.py [--sandbox]

Options:
    --sandbox   Run against the Sandbox catalog instead of AWS (production)
"""

import sys
import time
from partner_central_client import PartnerCentralClient


# All sample queries from the guide, organized by category
SAMPLE_QUERIES = [
    # Pipeline overview
    ("Pipeline overview", "List all my open opportunities"),
    ("Pipeline overview", "How many opportunities are closing next month?"),
    ("Pipeline overview", "Which opportunities need my attention this week?"),

    # Opportunity detail
    ("Opportunity detail", "Give me a summary of opportunity O14310233"),
    ("Opportunity detail", "What's the current stage and expected revenue for the Coder deal?"),

    # Sales strategy
    ("Sales strategy", "Generate a sales play for opportunity O14310233"),
    ("Sales strategy", "What are the next steps to advance opportunity O14310233?"),

    # Funding programs
    ("Funding programs", "Am I eligible for MAP funding on opportunity O14310233?"),
    ("Funding programs", "What funding programs are available for a POC?"),

    # Customer insights
    ("Customer insights", "Create a customer profile for Coder"),
    ("Customer insights", "Which of our solutions best match opportunity O14310233?"),

    # Loss analysis
    ("Loss analysis", "What are the top reasons we lost opportunities in the last 6 months?"),
]


def main():
    catalog = "Sandbox" if "--sandbox" in sys.argv else "AWS"

    print("=" * 70)
    print(f"PARTNER CENTRAL MCP - SAMPLE QUERY VALIDATION ({catalog} catalog)")
    print("=" * 70)
    print(f"\nTotal queries: {len(SAMPLE_QUERIES)}")
    print(f"Rate limit: 2 req/min sustained, burst 10")
    print(f"Strategy: burst first 8, then 32s spacing\n")

    try:
        client = PartnerCentralClient()
    except KeyError as e:
        print(f"ERROR: Missing environment variable: {e}")
        print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY before running.")
        sys.exit(1)

    client.initialize()
    results = []

    for i, (category, query) in enumerate(SAMPLE_QUERIES):
        # Rate limiting strategy
        if i > 0 and i % 8 == 0:
            print(f"\n--- Pausing 60s for rate limit reset ---\n")
            time.sleep(60)
        elif i > 8:
            time.sleep(32)

        print(f"[{i+1:2d}/{len(SAMPLE_QUERIES)}] {category}: \"{query}\"")

        try:
            response = client.send_message(query, catalog=catalog)
            success = response["status"] == "complete" and len(response["messages"]) > 0
            results.append({"success": success, "category": category, "query": query})

            if success:
                preview = response["messages"][-1][:120]
                print(f"       ✅ status=complete | msgs={len(response['messages'])}")
                print(f"       Preview: {preview}...")
            else:
                print(f"       ❌ status={response['status']} | msgs={len(response['messages'])}")

        except Exception as e:
            results.append({"success": False, "category": category, "query": query})
            print(f"       ❌ ERROR: {type(e).__name__}: {e}")

        print()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])
    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}\n")

    for r in results:
        icon = "✅" if r["success"] else "❌"
        print(f"  {icon} [{r['category']}] {r['query']}")

    if failed > 0:
        print(f"\n--- FAILED QUERIES ---")
        for r in results:
            if not r["success"]:
                print(f"  ❌ {r['query']}")
        sys.exit(1)
    else:
        print(f"\n🎉 All {passed} queries passed!")


if __name__ == "__main__":
    main()
