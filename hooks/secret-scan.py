#!/usr/bin/env python3
"""PostToolUse: warn when a secret appears in a tool call or its output; log it masked (last 4 chars) for rotation."""
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from common import load_config, state_file  # noqa: E402

CFG = load_config()
if not CFG["secret_scan"]:
    sys.exit(0)

PATTERNS = {
    "GitHub token": r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})",
    "GitLab token": r"\bgl(pat|oas|dt|rt|cbt|ptt|ft|imt|soat)-[A-Za-z0-9_.\-]{20,}",
    "AWS access key": r"\b(AKIA|ASIA)[A-Z0-9]{16}\b",
    "Google API key": r"\bAIza[0-9A-Za-z_\-]{35}\b",
    "Anthropic/OpenAI key": r"\bsk-(ant-)?[A-Za-z0-9_\-]{32,}",
    "Slack token": r"\bxox[abposr]-[A-Za-z0-9-]{10,}",
    "Vault token": r"\bhv[sbr]\.[A-Za-z0-9_\-]{24,}",
    "JWT": r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",
    "Private key": r"-----BEGIN (RSA |EC |OPENSSH |ENCRYPTED |DSA )?PRIVATE KEY-----",
    "Secret assignment": r"(?i)\b(password|passwd|secret|client_secret|api_key|apikey|access_token|token)\b[\"']?\s*[=:]\s*[\"']?(?![$<{%])[^\s\"',;]{16,}",
}

try:
    event = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
text = "\n".join(v if isinstance(v, str) else json.dumps(v) for v in (event.get("tool_input"), event.get("tool_response")) if v)
hits = {}
for kind, rx in PATTERNS.items():
    for m in re.finditer(rx, text):
        hits[f"{kind} (...{m.group(0)[-4:]})"] = kind
if not hits:
    sys.exit(0)
tool = event.get("tool_name", "?")
with open(state_file("exposed-secrets.log"), "a", encoding="utf-8") as f:
    for h in hits:
        f.write(f"{dt.datetime.now().isoformat(timespec='seconds')}\t{tool}\t{h}\tROTATE\n")
if CFG.get("security_note"):
    note = Path(CFG["security_note"]).expanduser()
    if not note.exists():
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(
            "---\ntype: analysis\ntitle: \"Secretos expuestos\"\n"
            "description: \"Registro de secretos expuestos en herramientas, con estado de rotación\"\n"
            "tags: [security, secrets, log]\n"
            f"timestamp: {dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}\nstatus: active\n---\n\n"
            "# Secretos expuestos\n\nSolo tipo y últimos 4 caracteres, nunca el valor. Cambia `pendiente de rotar` a `rotado` cuando lo hagas.\n\n"
            "| Fecha | Herramienta | Tipo | Últimos 4 | Estado |\n|---|---|---|---|---|\n",
            encoding="utf-8")
    with open(note, "a", encoding="utf-8") as f:
        for h in hits:
            kind, _, last4 = h.partition(" (...")
            f.write(f"| {dt.datetime.now():%Y-%m-%d %H:%M} | {tool} | {kind} | {last4.rstrip(')')} | pendiente de rotar |\n")
msg = f"SECRET EXPOSED in {tool}: {', '.join(hits)}. Rotate it. Logged masked in ~/.local/state/ai-knowledge/exposed-secrets.log"
print(json.dumps({
    "systemMessage": msg,
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": msg + " Say so in the first line of your reply (type and where, never the value) and keep reminding until the user confirms rotation.",
    },
}))
