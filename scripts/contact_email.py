#!/usr/bin/env python3
"""
Contact-email policy for outbound HTTP User-Agent headers.
Uses ONLY Python standard library.
"""

import os
import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# RFC 2606 / 6761 reserved names commonly copied from documentation
PLACEHOLDER_DOMAINS = {
    "example.com",
    "example.net",
    "example.org",
    "example.edu",
    "localhost",
    "invalid",
    "test",
}
PLACEHOLDER_TLDS = {"example", "invalid", "localhost", "test"}

CONTACT_EMAIL_SETUP_MESSAGE = """\
ERROR: Refusing to send HTTP requests. A real executor contact email is required in the User-Agent.

Rejected values: unset, empty, and documentation placeholders
(e.g. you@example.com, *@example.org, *@example.net).

What the agent should do next:
1. Ask the user for their own contact email (institutional address preferred).
2. Set it in the current shell. Do not commit it to git:
     export SCHOLARLY_CONTACT_EMAIL="firstname.lastname@university.ac.jp"
3. Re-run the same command. Do not invent an address or reuse example.com.

Optional: set "contact_email" in config/literature_providers.json for this machine only.
SCHOLARLY_CONTACT_EMAIL takes precedence when both are set.

エラー: 外部 HTTP リクエストを中止しました。User-Agent に実行者本人の連絡先メールが必要です。
未設定・空文字・ドキュメント用ダミー（example.com 等）は拒否します。
ユーザーに実メールを確認し、上記 export を設定してから同じコマンドを再実行してください。
"""


class ContactEmailError(ValueError):
    """Raised when outbound HTTP is blocked because no usable contact email is set."""


def resolve_contact_email(config: dict = None) -> str:
    """Prefer SCHOLARLY_CONTACT_EMAIL, then config contact_email. Never invent an address."""
    env_email = os.environ.get("SCHOLARLY_CONTACT_EMAIL", "").strip()
    if env_email:
        return env_email
    if config:
        return str(config.get("contact_email") or "").strip()
    return ""


def _email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower().rstrip(".")


def is_usable_contact_email(email: str) -> bool:
    """Return True only for a syntactically valid, non-placeholder address."""
    candidate = (email or "").strip()
    if not candidate or not EMAIL_PATTERN.match(candidate):
        return False
    domain = _email_domain(candidate)
    if domain in PLACEHOLDER_DOMAINS:
        return False
    tld = domain.rsplit(".", 1)[-1]
    if tld in PLACEHOLDER_TLDS:
        return False
    return True


def require_contact_email(config: dict = None) -> str:
    """Return a usable contact email or raise ContactEmailError before any HTTP call."""
    email = resolve_contact_email(config)
    if not is_usable_contact_email(email):
        raise ContactEmailError(CONTACT_EMAIL_SETUP_MESSAGE)
    return email
