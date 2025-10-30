## Feature Ideas (no infrastructure changes required)

Below are practical feature ideas you can implement without changing AWS infrastructure. For each idea I list where to edit or add code in this repository.

- Prompt tuning and creative modes
  - Files: `lambda/anthropic_client.py` — add prompt templates and mode selectors (short/long/poetic).

- Per-recipient personalization
  - Files: `config/recipients.json`, `lambda/email_formatter.py`, `lambda/handler.py` — add optional fields (name, timezone, preferred_length, delivery_flags) and apply per-recipient formatting.

- Robust fallback content
  - Files: `lambda/anthropic_client.py`, `lambda/quote_tracker.py`, `config/stoic_quotes_365_days.json` — fall back to curated quotes/templates when model calls fail or produce unsafe output.

- Retry & backoff for Anthropic calls
  - Files: `lambda/anthropic_client.py` — implement exponential backoff, jitter, and limited retries.

- Length / style enforcement & post-processing
  - Files: `lambda/anthropic_client.py`, `lambda/email_formatter.py` — post-process responses to enforce length, remove offensive words, and normalize punctuation.

- Improve email UX & accessibility
  - Files: `lambda/email_formatter.py` — enhance responsive templates, inline CSS, plain-text parity, and alt text.

- Local dev mocks & test harness
  - Files: new `lambda/mock_anthropic.py`, CLI runner in `tests/` or small `scripts/` folder — allow running the handler with deterministic outputs.

- Expand unit/integration tests
  - Files: `tests/test_anthropic_client.py`, `tests/test_email_formatter.py`, `tests/test_safety.py` — add coverage for prompt-building, parsing, formatting, and safety checks.

- Structured logging & correlation IDs
  - Files: `lambda/handler.py`, `lambda/anthropic_client.py` — add JSON logs and per-request correlation IDs.

- Cache S3/config reads within invocation
  - Files: `lambda/quote_loader.py`, `lambda/handler.py` — cache loaded JSON files in `/tmp` or an in-memory dict for the Lambda invocation.

- Metrics & observability
  - Files: `lambda/handler.py`, `lambda/anthropic_client.py` — emit PutMetricData calls for latencies, failures, and fallback usage.

- Digest/weekly mode & scheduling flags
  - Files: `config/recipients.json`, `lambda/handler.py` — add flags for weekly digests or weekday-only delivery and honor them in the handler.

- Prompt templates per monthly theme
  - Files: `lambda/themes.py`, `lambda/anthropic_client.py` — alternate prompt templates per theme for richer variety.


## Strong Security Controls for Handling Untrusted Model Output

Context and problem statement

The Anthropic API (or any generative model) produces stochastic outputs. Even with tightly controlled inputs, outputs can include profanity, PII, instructions, malicious payloads (e.g., URLs leading to exfiltration), or content that violates policy. You need a robust, defense-in-depth pipeline that detects, classifies, sanitizes, records, and alerts on suspicious outputs before they are sent to end users.

High-level goals

- Prevent delivery of harmful content (profanity, hate, disallowed instructions).
- Detect PII or secrets and prevent accidental disclosure.
- Alert and create an auditable trail for suspicious responses.
- Provide a safe fallback path when output is unsafe.
- Make detection observable and testable.

Threat model (examples)

- Stochastic toxic content (insults, hate speech).
- Instructions for wrongdoing or unsafe actions embedded in a meditation message.
- Outputs containing e.g. credit card numbers, SSNs, private email addresses, API keys.
- Links to malicious websites or prompting users to run commands.
- HTML/script injection in rich HTML emails or crafted attachments.

Design overview — safe response pipeline

1. Response Normalization
   - Trim whitespace, normalize unicode, remove invisible characters, and strip out control characters.
2. Deterministic scanners
   - Run allowlist/blocklist checks (regex for SSN, credit card, phone, known bad domains), profanity lists, and known disallowed phrases.
3. Machine/semantic classifiers
   - Use a local/lightweight classifier or an external safety model to score toxicity, instruction-intent, and PII likelihood. Thresholds trigger blocking or human review.
4. URL & domain safety checks
   - Extract URLs, resolve and scan domains against threat lists (Google Safe Browsing or internal allowlist) before rendering them as links.
5. HTML sanitization
   - If sending HTML emails, sanitize using a strict HTML sanitizer (allow only minimal tags and attributes; strip out scripts, iframes, onclicks).
6. Policy decisions and actions
   - PASS: send as-is (maybe with minor cleanup).
   - WARN: redact or truncate sections and send with a warning banner.
   - BLOCK: do not send; instead use fallback content and escalate/alert.
7. Logging, metrics, and alerts
   - Emit structured logs with correlation IDs, a safety score, and the decision outcome (PASS/WARN/BLOCK). Increment metrics (safety_block_count, safety_warn_count) and raise alarms when thresholds exceeded.
8. Human-in-the-loop quarantine
   - For high-risk outputs, save the response and alert a reviewer (store in a safe S3 prefix or a private admin dashboard) for manual approval.

Concrete controls and implementation notes (file-level mapping)

- Add a new safety module
  - File: `lambda/content_safety.py` (new)
  - Responsibilities:
    - normalize_text(text) -> str
    - run_regex_detectors(text) -> List[flags]
    - run_pii_detector(text) -> List[pii_types]
    - run_toxicity_classifier(text) -> score
    - sanitize_html(html) -> safe_html
    - decide_action(scores, flags) -> {action, reason, remediation}

- Hook into the pipeline
  - File edits: `lambda/anthropic_client.py`, `lambda/handler.py`, `lambda/email_formatter.py`
  - Flow: after receiving the model response in `anthropic_client`, call `content_safety.normalize_text()` and the detectors. Use the result to decide whether to return the original, a sanitized version, or signal a BLOCK to `handler`.

- Fallback behavior
  - File: `lambda/quote_tracker.py` / `lambda/anthropic_client.py`
  - Behavior: if BLOCK, pick a safe fallback from `config/stoic_quotes_365_days.json` and mark the record in the tracker (visibility into fallback_count).

- Alerting & observability
  - File: `lambda/handler.py`
  - Behavior: when action != PASS, create structured CloudWatch logs (JSON) with correlation_id, recipient_id, safety_action, and snippet (if safe). Emit a metric via PutMetricData for safety_block or safety_warn. For serious events, publish to an SNS topic (or email/SMS) — wiring this requires no infra change if you have an SNS topic ARN in config, or you can use CloudWatch Alarms on the emitted metric.

- Human review queue
  - Artifact: S3 prefix (e.g., s3://<bucket>/safety-quarantine/YYYY/MM/DD/<id>.json) containing the response, metadata, and original prompt. A reviewer service or script can list objects and approve/reject.

- Runtime sanitization for HTML emails
  - File: `lambda/email_formatter.py`
  - Use a robust sanitizer (Bleach or similar) and then whitelist only basic tags (<p>, <strong>, <em>, <ul>, <li>, <a href>) and only allow hrefs that pass domain checks. Remove images or attachments unless explicitly allowed.

- PII and secrets detection
  - Implement regex detectors for common patterns (SSN, credit card, API keys) and a named-entity recognizer for names, emails, and phone numbers (spaCy or a lightweight rule-based approach). Treat matches as high-severity and BLOCK by default.

- URLs and link handling
  - Extract links, resolve redirects (careful with outgoing network calls — do this asynchronously or on demand), and check against threat lists or an allowlist configured in `config/` (e.g., `config/allowed_domains.json`). If a link is suspicious, remove/replace link text with plain text and add a warning.

- Rate limiting and throttling
  - If model outputs trigger many safety events (surge in warnings/blocks), throttle outbound sends and raise an operational alert to investigate possible prompt drift or model issues.

- Incident response & playbook
  - Create a short runbook (README or doc) explaining steps when an unsafe message was sent: identify recipients, revoke or follow up, notify stakeholders, patch prompt/template, rotate any leaked keys, and file a postmortem.

Testing, validation, and continuous assurance

- Unit tests
  - Files: `tests/test_safety.py` — cover regex detectors, PII detection, HTML sanitizer, and policy decisions. Include edge cases (embedded numbers, obfuscated tokens).

- Fuzzing and red-team tests
  - Create a test harness that generates adversarial outputs (obfuscated PII, crafted HTML/JS, nested instructions) to validate detection thresholds.

- Canary and staged rollout
  - Add a config flag to route a small percentage of recipients through a stricter safety pipeline or human review path. Use this to validate before full rollout.

- Monitoring and dashboards
  - Instrument metrics: safety_pass_count, safety_warn_count, safety_block_count, fallback_count, safety_latency.
  - Build a dashboard (CloudWatch or Grafana) visualizing trends and alert on spikes.

Operational considerations and best practices

- Store safety rules/config in `config/` (e.g., `config/safety_policies.json`) so updates don't require code changes.
- Keep a tamper-evident audit log for every model response and final outgoing content; log only redacted snippets when necessary to avoid storing PII.
- Apply least privilege for any service that reads the quarantine bucket and for any SNS/topic used for alerts.
- Ensure logs do not leak sensitive content; redact secrets and PII before writing to broad-access logs.
- Maintain a rollback/kill-switch (config flag or parameter) to pause automated sends if policy errors occur.

Minimal example implementation plan (low-risk start)

1. Add `lambda/content_safety.py` containing:
   - normalization, regex detectors, HTML sanitizer wrapper, and a simple classification step (score thresholds).
2. Wire `content_safety` into `lambda/anthropic_client.py` so every response is checked before returning to `handler`.
3. Update `lambda/handler.py` to: log safety decisions, increment metrics, and use fallback content on BLOCK.
4. Add tests in `tests/test_safety.py` for the basic detectors.
5. Add `config/safety_policies.json` to control thresholds and allowlist/blocklist rules.

References and quick checklist

- Add files:
  - `lambda/content_safety.py` (new)
  - `config/safety_policies.json` (new)
  - `tests/test_safety.py` (new)

- Edit files:
  - `lambda/anthropic_client.py` (call safety checks)
  - `lambda/handler.py` (metrics, logging, fallback)
  - `lambda/email_formatter.py` (HTML sanitization)

- Quick checklist before deploying changes to production:
  - ✅ Unit tests for detectors and sanitizers
  - ✅ Canary rollout to a small percentage of recipients
  - ✅ CloudWatch metrics and dashboards created
  - ✅ Runbook and alerting configured (SNS/Email)

If you’d like, I can implement the minimal starter pieces now: create `lambda/content_safety.py`, hook it into `lambda/anthropic_client.py`, and add a basic `tests/test_safety.py`. Tell me which level of automation you want (just detection + fallback, or detection + human-review queue). Otherwise I can iterate on the policy JSON and detailed test cases next.

---

End of file.
