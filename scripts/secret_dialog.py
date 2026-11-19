#!/usr/bin/env python3
"""Ask for a secret in a native masked dialog and save it as KEY=value in a file (mode 600).

  secret_dialog.py --file PATH --key NAME [--label TEXT]

The value goes from the dialog to this process and into the file; it is never printed.
Dialog by system: WSL or Windows (powershell.exe), macOS (osascript), Linux (zenity or kdialog).
Only the WSL/Windows branch has been run; the others are untested.
"""
import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WINDOWS_DIALOG = r"""
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.Form
$f.Text = 'ai-knowledge'; $f.Width = 460; $f.Height = 240; $f.StartPosition = 'CenterScreen'
$l = New-Object System.Windows.Forms.Label
$l.Text = [IO.File]::ReadAllText($args[0], [Text.Encoding]::UTF8); $l.Left = 10; $l.Top = 10; $l.Width = 430; $l.Height = 90
$t = New-Object System.Windows.Forms.TextBox
$t.UseSystemPasswordChar = $true; $t.Left = 10; $t.Top = 105; $t.Width = 430
$c = New-Object System.Windows.Forms.CheckBox
$c.Text = 'Mostrar lo que escribo'; $c.Left = 10; $c.Top = 140; $c.Width = 200
$c.Add_CheckedChanged({ $t.UseSystemPasswordChar = -not $c.Checked })
$b = New-Object System.Windows.Forms.Button
$b.Text = 'Guardar'; $b.Left = 340; $b.Top = 135; $b.DialogResult = 'OK'
$f.AcceptButton = $b; $f.Controls.AddRange(@($l, $t, $c, $b))
if ($f.ShowDialog() -eq 'OK') { [Console]::Out.Write($t.Text) }
"""


def is_wsl():
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def ask_windows(label):
    """Writes the dialog script and the label to temp files, then runs PowerShell on the script file.
    Passing the script on the command line breaks on quotes and newlines; a file does not."""
    workdir = Path(tempfile.mkdtemp(prefix="ak-dialog-"))
    try:
        script_file = workdir / "dialog.ps1"
        label_file = workdir / "label.txt"
        script_file.write_text(WINDOWS_DIALOG, encoding="utf-8-sig")
        label_file.write_text(label.replace("\n", " · "), encoding="utf-8")
        win = lambda path: subprocess.run(["wslpath", "-w", str(path)], capture_output=True, text=True).stdout.strip()
        out = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-STA", "-File", win(script_file), win(label_file)],
            capture_output=True, text=True, encoding="utf-8", check=False)
        if out.returncode != 0 and out.stderr.strip():
            sys.exit(f"Windows dialog failed: {out.stderr.strip()[:300]}")
        return out.stdout.strip()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def ask_secret(label):
    if is_wsl() and shutil.which("powershell.exe"):
        return ask_windows(label)
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
    parser.add_argument("--base64-user", action="store_true",
                        help="store base64(':' + value), as Azure DevOps MCP expects")
    parser.add_argument("--also", help="also store the same value under this variable (vSphere)")
    parser.add_argument("--detach", action="store_true",
                        help="return at once; the dialog keeps running and saves the value by itself")
    args = parser.parse_args()

    if args.detach:
        # The panel waits only for this call. The dialog runs in a detached child that saves the value.
        child_args = [sys.executable, __file__] + [a for a in sys.argv[1:] if a != "--detach"]
        log = Path(os.path.expanduser("~/.local/state/ai-knowledge/secret-dialog.log"))
        log.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with open(log, "a", encoding="utf-8") as logf:
            subprocess.Popen(child_args, start_new_session=True, stdout=logf, stderr=logf)
        print(f"Ventana abierta para {args.key}. Pega el valor allí; se guarda sola en {args.file}.")
        return

    value = ask_secret(f"{args.key}: {args.label}")
    if not value:
        sys.exit("Empty value or dialog cancelled: nothing saved.")

    stored = base64.b64encode(f":{value}".encode()).decode() if args.base64_user else value
    path = Path(os.path.expanduser(args.file))
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    text = upsert(text, args.key, stored)
    if args.also:
        text = upsert(text, args.also, value)
    path.write_text(text, encoding="utf-8")
    os.chmod(path, 0o600)
    print(f"Saved {args.key} in {path} (mode 600).")


if __name__ == "__main__":
    main()
