# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.2.x | ✅ Yes |

## Reporting a Vulnerability

If you discover a security vulnerability in DocStruct, please report it by opening a GitLab issue with the label `security`. Do not disclose security vulnerabilities publicly until they have been addressed.

## Data Privacy

DocStruct is designed to process documents locally — no data is sent to external servers during the core pipeline. The `ollama` backend communicates with a local server on `localhost` only. The `mock` backend makes no network calls at all. See `tests/test_no_network.py` for the automated proof.
