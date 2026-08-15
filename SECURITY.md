# Security Policy

## Supported versions

Security fixes are accepted against the default `main` branch.

## Reporting a vulnerability

Please **do not** open a public issue for vulnerabilities that could expose credentials, private research data, or remote code execution.

Use GitHub's **Security Advisory** (Privately report a vulnerability) on this repository. Include:

- Affected file or script
- Steps to reproduce
- Impact (data leak, command injection, path traversal, etc.)
- A suggested fix if you have one

We will acknowledge the report and discuss a fix timeline in the advisory thread.

## What is in scope

- Secrets or PII accidentally committed to this repository
- Path traversal or command injection in `scripts/`
- Ignore-file gaps that would cause raw research data to be indexed or committed when users follow the documented setup

## What is out of scope

- Hallucinated citations produced by a host LLM (this is an agent-discipline problem; use `claim-evidence-gate` and `citation-traceability-audit`)
- Rate limits or blocks from third-party APIs (OpenAlex, Crossref, Semantic Scholar, World Bank)
- Academic misconduct by end users
