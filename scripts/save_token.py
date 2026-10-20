"""Save a Moodle web service token obtained through the Moodle app's sign-in launch.

For sites that use single sign-on, the "Moodle mobile web service" key is created by the
Moodle app's launch page, which redirects to a  moodlemobile://token=...  address.
Paste that whole address into  data/launch.txt  and run:  python scripts/save_token.py

The token is written to .env and launch.txt is deleted. The token is never printed.
"""
import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAUNCH = ROOT / "data" / "launch.txt"
ENV = ROOT / ".env"


def main():
    if not LAUNCH.exists():
        sys.exit(f"Not found: {LAUNCH}")
    match = re.search(r"token=([A-Za-z0-9+/=_-]+)", LAUNCH.read_text(encoding="utf-8"))
    if not match:
        sys.exit("No 'token=' found in launch.txt - copy the whole moodlemobile://token=... address.")
    encoded = match.group(1)
    decoded = base64.b64decode(encoded + "=" * (-len(encoded) % 4)).decode("utf-8", "replace")
    parts = decoded.split(":::")  # signature ::: token [::: private token]
    if len(parts) < 2 or not re.fullmatch(r"[0-9a-f]{32}", parts[1]):
        sys.exit("That address didn't contain a token in the expected format.")

    text = ENV.read_text(encoding="utf-8") if ENV.exists() else "MOODLE_TOKEN=\n"
    if re.search(r"(?m)^MOODLE_TOKEN=", text):
        text = re.sub(r"(?m)^MOODLE_TOKEN=.*$", f"MOODLE_TOKEN={parts[1]}", text)
    else:
        text += f"\nMOODLE_TOKEN={parts[1]}\n"
    ENV.write_text(text, encoding="utf-8")
    LAUNCH.unlink()
    print("Token saved to .env (launch.txt deleted).")


if __name__ == "__main__":
    main()
