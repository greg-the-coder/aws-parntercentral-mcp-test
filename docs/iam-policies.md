# IAM Policy Reference

## Read-Only Policy: `coder-partner-mcp-readonly`

**ARN:** `arn:aws:iam::<your-account-id>:policy/coder-partner-mcp-readonly`

This policy grants:
- MCP session access (required for all MCP communication)
- Read-only Partner Central operations (list/get opportunities, solutions, etc.)
- Marketplace query permissions (describe entities, search agreements)

### Policy Document

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

### Attach to a User

```bash
aws iam attach-user-policy \
    --user-name <your-iam-user> \
    --policy-arn arn:aws:iam::<your-account-id>:policy/coder-partner-mcp-readonly
```

### Attach to a Role

```bash
aws iam attach-role-policy \
    --role-name <your-role-name> \
    --policy-arn arn:aws:iam::<your-account-id>:policy/coder-partner-mcp-readonly
```

---

## Full Access Policy (for write operations)

If your agent needs to create/update opportunities or submit funding applications, use an expanded policy. **Note:** `coder-partner-mcp-readonly` is sufficient for all read queries.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "partnercentral:UseSession",
                "partnercentral:List*",
                "partnercentral:Get*",
                "partnercentral:CreateOpportunity",
                "partnercentral:UpdateOpportunity",
                "partnercentral:SubmitOpportunity",
                "partnercentral:AssignOpportunity",
                "partnercentral:AssociateOpportunity",
                "partnercentral:DisassociateOpportunity",
                "partnercentral:CreateBenefitApplication",
                "partnercentral:UpdateBenefitApplication",
                "partnercentral:SubmitBenefitApplication",
                "partnercentral:AmendBenefitApplication",
                "partnercentral:CancelBenefitApplication",
                "partnercentral:RecallBenefitApplication",
                "partnercentral:AssociateBenefitApplicationResource",
                "partnercentral:DisassociateBenefitApplicationResource"
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

---

## AWS Managed Policy Alternative

For quick setup, AWS provides the `AWSMcpServiceActionsFullAccess` managed policy which includes all permissions needed to interact with the MCP server.

---

## Permissions Breakdown

| Action | Purpose | Needed For |
|--------|---------|------------|
| `partnercentral:UseSession` | Create/update/retrieve MCP sessions | All MCP communication |
| `partnercentral:List*` | List opportunities, solutions, benefits, etc. | Pipeline queries |
| `partnercentral:Get*` | Get details of specific resources | Opportunity summaries |
| `partnercentral:CreateOpportunity` | Create new opportunities | Write operations |
| `partnercentral:UpdateOpportunity` | Modify opportunity fields | Write operations |
| `partnercentral:SubmitOpportunity` | Submit for AWS review | Write operations |
| `partnercentral:*BenefitApplication` | Funding program operations | MAP/POC/WMP requests |
| `aws-marketplace:DescribeEntity` | View marketplace entities | Marketplace queries |
| `aws-marketplace:SearchAgreements` | Search agreements | Marketplace queries |
| `aws-marketplace:ListEntities` | List marketplace entities | Marketplace queries |
