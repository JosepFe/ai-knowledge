#!/usr/bin/env python3
"""Ask for a secret in a native masked dialog and save it as KEY=value in a file (mode 600).

  secret_dialog.py --file PATH --key NAME [--label TEXT]

The value goes from the dialog to this process and into the file; it is never printed.
Dialog by system: WSL or Windows (powershell.exe), macOS (osascript), Linux (zenity or kdialog).
Only the WSL/Windows branch has been run; the others are untested.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

WINDOWS_DIALOG = r"""
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.Form
$f.Text = 'ai-knowledge'; $f.Width = 440; $f.Height = 160; $f.StartPosition = 'CenterScreen'
$l = New-Object System.Windows.Forms.Label
$l.Text = '__LABEL__'; $l.Left = 10; $l.Top = 10; $l.Width = 400
$t = New-Object System.Windows.Forms.TextBox
$t.UseSystemPasswordChar = $true; $t.Left = 10; $t.Top = 40; $t.Width = 400
$b = New-Object System.Windows.Forms.Button
$b.Text = 'Guardar'; $b.Left = 320; $b.Top = 75; $b.DialogResult = 'OK'
$f.AcceptButton = $b; $f.Controls.AddRange(@($l, $t, $b))
if ($f.ShowDialog() -eq 'OK') { [Console]::Out.Write($t.Text) }
"""


def is_wsl():
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def ask_secret(label):
    if is_wsl() and shutil.which("powershell.exe"):
        script = WINDOWS_DIALOG.replace("__LABEL__", label.replace("'", "''"))
        out = subprocess.run(["powershell.exe", "-NoProfile", "-STA", "-Command", script],
                             capture_output=True, text=True, check=False)
        return out.stdout.strip()
    if sys.platform == "darwin":
        script = f'display dialog "{label}" default answer "" with hidden answer with title "ai-knowledge"'
        out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        marker = "text returned:"
        return out.stdout.split(marker, 1)[1].strip() if marker in out.stdout else ""
    if shutil.which("zenity"):
        out = subprocess.run(["zenity", "--password", f"--text={label}"], capture_output=True, text=True, check=False)
        return out.stdout.strip()
    if shutil.which("kdialog"):
        out = subprocess.run(["kdialog", "--password", label], capture_output=True, text=True, check=False)
        return out.stdout.strip()
    sys.exit("No dialog tool found (zenity or kdialog on Linux). Use the terminal instead.")


def upsert(text, key, value):
    lines = [line for line in text.split("\n") if line != ""]
    found = any(line.startswith(f"{key}=") for line in lines)
    out = [f"{key}={value}" if line.startswith(f"{key}=") else line for line in lines]
    return "\n".join(out + ([] if found else [f"{key}={value}"])) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--label", default="Pega el valor y pulsa Guardar")
    args = parser.parse_args()

    value = ask_secret(f"{args.key}: {args.label}")
    if not value:
        sys.exit("Empty value or dialog cancelled: nothing saved.")

    path = Path(os.path.expanduser(args.file))
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(upsert(text, args.key, value), encoding="utf-8")
    os.chmod(path, 0o600)
    print(f"Saved {args.key} in {path} (mode 600).")


if __name__ == "__main__":
    main()
