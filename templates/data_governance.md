# Data Governance Register

Project: <short name>
Owner: <data owner>
Last updated (Beijing): <YYYY-MM-DD HH:MM>

## 1. Data Classification

| Source | Public / restricted / confidential | PII? | DUA/license? | IRB/ethics? | Public package action |
|---|---|---:|---|---|---|
| <source> | <type> | no | <terms> | <approval/exemption> | include / script-only / exclude |

Classification rules:

- Public: can be redistributed under the stated license.
- Restricted: third parties can apply for access, but raw data cannot be redistributed.
- Confidential: raw or analysis data cannot leave the approved environment.
- PII: direct or indirect personal identifiers are present or can reasonably re-identify people.

## 2. Access and Handling

- Approved storage location:
- Approved compute environment:
- Who may access:
- Files excluded from git/archive:
- De-identification or aggregation steps:
- Retention / deletion rule:

## 3. Archive Boundary

Public replication package may include:

- Code:
- Synthetic or public sample data:
- Derived analysis data:
- Documentation:

Public replication package must not include:

- Restricted raw data:
- PII or quasi-identifiers:
- Credentials, tokens, signed URLs:
- DUA/IRB-restricted confidential materials:

## 4. Disclosure Inputs

- DAS text source:
- IRB/ethics disclosure:
- Data citation:
- License statement:
- Contact or application procedure for restricted data:
- Expected cost and approval time:

## 5. Gate Consequences

- If raw restricted data is present in a public package: stop and remove before submission.
- If PII is present in logs, tables, or examples: stop and sanitize before continuing.
- If access conditions are unknown: replication status is not_ready.
- If IRB/DUA terms conflict with public deposit: use script-only or controlled-access disclosure.
