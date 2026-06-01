# Cloud Audit Log Detection Query Examples

This reference holds control-plane audit-log detections for each major cloud, organized by the high-value abuse patterns the parent SKILL.md targets: privileged or root API use, IAM policy and role changes that escalate privilege or create persistence, and tampering that disables logging or guardrails. For each cloud, the snippets are vendor-native because control-plane schemas are not portable the way endpoint process events are: AWS CloudTrail, Azure Activity and Entra audit logs (queried with KQL), and GCP Audit Logs each name the actor, action, target, and outcome differently. Normalize them to a common shape (actor, action, target, source, outcome, time) in your pipeline, then apply these per-cloud detections. All identifiers and resource names below are obviously fake placeholders; re-author them and the suppression allow-lists for your own accounts before shipping.

## AWS CloudTrail

CloudTrail records control-plane API calls. Query it through Athena (SQL) or your SIEM. The patterns below cover root usage, IAM persistence, privilege escalation by policy attachment, and logging tamper.

### Root account API use

Root should almost never be used for day-to-day API calls; any non-console root activity is high severity.

```sql
SELECT eventtime, eventname, sourceipaddress, useragent, awsregion
FROM cloudtrail_logs
WHERE useridentity.type = 'Root'
  AND eventtype <> 'AwsServiceEvent'
  AND eventname NOT IN ('GetSessionToken', 'ConsoleLogin')
ORDER BY eventtime DESC;
```

### IAM persistence (new access key creation)

A `CreateAccessKey` call for a principal outside the normal change window is a common persistence step. Correlate with a preceding `CreateUser` for stronger signal.

```sql
SELECT eventtime, useridentity.arn AS actor, eventname,
       json_extract_scalar(responseelements, '$.accessKey.userName') AS target_user,
       sourceipaddress
FROM cloudtrail_logs
WHERE eventname IN ('CreateAccessKey', 'CreateUser', 'CreateLoginProfile')
  AND useridentity.arn NOT LIKE '%:user/approved-automation%'
ORDER BY eventtime DESC;
```

### Privilege escalation (admin-equivalent policy attached)

```sql
SELECT eventtime, useridentity.arn AS actor, eventname,
       json_extract_scalar(requestparameters, '$.policyArn') AS policy_arn,
       json_extract_scalar(requestparameters, '$.userName') AS target_principal
FROM cloudtrail_logs
WHERE eventname IN ('AttachUserPolicy', 'AttachRolePolicy', 'PutUserPolicy', 'PutRolePolicy')
  AND (json_extract_scalar(requestparameters, '$.policyArn') = 'arn:aws:iam::aws:policy/AdministratorAccess'
       OR json_extract_scalar(requestparameters, '$.policyDocument') LIKE '%"Action":"*"%')
ORDER BY eventtime DESC;
```

### Logging tamper (CloudTrail disabled or deleted)

Treat any trail stop, delete, or reconfiguration as high severity until attributed to an approved change.

```sql
SELECT eventtime, useridentity.arn AS actor, eventname,
       json_extract_scalar(requestparameters, '$.name') AS trail_name,
       sourceipaddress
FROM cloudtrail_logs
WHERE eventname IN ('StopLogging', 'DeleteTrail', 'UpdateTrail', 'PutEventSelectors')
ORDER BY eventtime DESC;
```

## Azure Activity and Entra Audit Logs (KQL)

Azure control-plane writes to `AzureActivity`; directory and IAM changes write to the Entra `AuditLogs`. Query both with KQL.

### Privileged role assignment (Entra)

Assigning a high-privilege directory role (for example, Global Administrator) outside an approved process is a privilege-escalation signal.

```kql
AuditLogs
| where OperationName == "Add member to role"
| extend RoleName = tostring(TargetResources[0].displayName)
| where RoleName has_any ("Global Administrator", "Privileged Role Administrator", "Application Administrator")
| extend Actor = tostring(InitiatedBy.user.userPrincipalName)
| where Actor !in ("approved-pim-automation@example.com")
| project TimeGenerated, Actor, RoleName, Result, IPAddress = tostring(InitiatedBy.user.ipAddress)
| sort by TimeGenerated desc
```

### Resource-level role change (Azure Activity)

```kql
AzureActivity
| where OperationNameValue endswith "roleAssignments/write"
   or OperationNameValue endswith "roleDefinitions/write"
| where ActivityStatusValue == "Success"
| project TimeGenerated, Caller, OperationNameValue, ResourceGroup, CallerIpAddress
| sort by TimeGenerated desc
```

### Logging tamper (diagnostic setting deleted)

```kql
AzureActivity
| where OperationNameValue endswith "diagnosticSettings/delete"
   or OperationNameValue endswith "logProfiles/delete"
| project TimeGenerated, Caller, OperationNameValue, _ResourceId, CallerIpAddress
| sort by TimeGenerated desc
```

## GCP Audit Logs

GCP Cloud Audit Logs (Admin Activity and Data Access) carry `protoPayload.methodName` and `protoPayload.authenticationInfo.principalEmail`. Query through Log Analytics (SQL) or a logs-based filter.

### IAM policy change (privilege escalation or persistence)

`SetIamPolicy` is the central privilege-granting call; a change by a non-approved principal warrants review, especially one that adds a primitive Owner or Editor role.

```sql
SELECT timestamp,
       proto_payload.audit_log.authentication_info.principal_email AS actor,
       proto_payload.audit_log.method_name AS method,
       proto_payload.audit_log.resource_name AS target
FROM `project.dataset.cloudaudit_googleapis_com_activity`
WHERE proto_payload.audit_log.method_name = 'SetIamPolicy'
  AND proto_payload.audit_log.authentication_info.principal_email NOT LIKE '%@approved-pipeline.iam.gserviceaccount.com'
ORDER BY timestamp DESC;
```

### Service account key creation (persistence)

```sql
SELECT timestamp,
       proto_payload.audit_log.authentication_info.principal_email AS actor,
       proto_payload.audit_log.method_name AS method,
       proto_payload.audit_log.resource_name AS target_sa
FROM `project.dataset.cloudaudit_googleapis_com_activity`
WHERE proto_payload.audit_log.method_name = 'google.iam.admin.v1.CreateServiceAccountKey'
ORDER BY timestamp DESC;
```

### Logging tamper (sink or bucket deleted)

```sql
SELECT timestamp,
       proto_payload.audit_log.authentication_info.principal_email AS actor,
       proto_payload.audit_log.method_name AS method,
       proto_payload.audit_log.resource_name AS target
FROM `project.dataset.cloudaudit_googleapis_com_activity`
WHERE proto_payload.audit_log.method_name IN (
        'google.logging.v2.ConfigServiceV2.DeleteSink',
        'google.logging.v2.ConfigServiceV2.UpdateSink',
        'storage.buckets.delete')
ORDER BY timestamp DESC;
```

## Adapting these examples

- Confirm log coverage first: a detection over a single-region or management-event-only trail produces false confidence. Verify which accounts, regions, and log sources are in scope before trusting any query.
- Replace each suppression clause (the `NOT LIKE` and `!in` allow-lists) with the real approved automation principals and change windows in your environment, and log suppressed matches rather than silently dropping them.
- Corroborate across events before alerting: a role creation followed by an access-key creation followed by a data export from one actor is far stronger signal than any single event. Emit each alert with the actor, action sequence, evidence event IDs, source context, severity, and a triage verdict, and keep these queries as version-controlled detection-as-code.
