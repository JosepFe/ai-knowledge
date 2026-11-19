#!/usr/bin/env python3
"""UserPromptSubmit: warn when a chat message seems to contain a password, even a short one.

Only warns and logs. It does not block the message and never stores the value: the log and the
vault note keep the type and the length, not the characters.
"""
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

# A keyword, an optional "is/es/:/=", then a value of at least 3 characters.
PASSWORD = re.compile(
    r"(?i)\b(contrase(?:ñ|n)a|password|passwd|pwd|clave)\b[^\n]{0,40}?(?:\b(?:es|is)\s+|[:=]\s*)[\"']?([^\s\"',;]{3,})")

try:
    event = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
prompt = event.get("prompt") or ""
matches = [m.group(1).lower() for m in PASSWORD.finditer(prompt)]
if not matches:
    sys.exit(0)

lengths = [len(m.group(2)) for m in PASSWORD.finditer(prompt)]
hits = [f"password ({n} characters)" for n in lengths]
now = dt.datetime.now()

with open(state_file("exposed-secrets.log"), "a", encoding="utf-8") as f:
    for h in hits:
        f.write(f"{now.isoformat(timespec='seconds')}\tchat\t{h}\tROTATE\n")

if CFG.get("security_note"):
    note = Path(CFG["security_note"]).expanduser()
    if not note.exists():
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(
            "---\ntype: analysis\ntitle: \"Secretos expuestos\"\n"
            "description: \"Registro de secretos expuestos en herramientas, con estado de rotación\"\n"
            "tags: [security, secrets, log]\n"
            f"timestamp: {now:%Y-%m-%dT%H:%M:%S}\nstatus: active\n---\n\n"
            "# Secretos expuestos\n\nSolo tipo y últimos 4 caracteres, nunca el valor. Cambia `pendiente de rotar` a `rotado` cuando lo hagas.\n\n"
            "| Fecha | Herramienta | Tipo | Últimos 4 | Estado |\n|---|---|---|---|---|\n",
            encoding="utf-8")
    with open(note, "a", encoding="utf-8") as f:
        for h in hits:
            f.write(f"| {now:%Y-%m-%d %H:%M} | chat | {h} | - | pendiente de rotar |\n")

msg = ("POSSIBLE PASSWORD in chat message: " + ", ".join(hits) +
       ". It was sent to the model. Rotate it if it is real. Logged without the value.")
print(json.dumps({
    "systemMessage": msg,
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": msg + " Say so in the first line of your reply (type only, never the value) and keep reminding until the user confirms rotation.",
    },
}))
