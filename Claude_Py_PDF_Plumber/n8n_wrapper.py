"""
n8n_wrapper.py
--------------
Drop this in the same directory as adobe_sign_extractor.py.
Called by n8n's "Execute Command" node.

n8n node configuration:
  Command:  python3 /opt/scripts/n8n_wrapper.py
  Stdin:    {{ $binary.data }}   (base64-encoded PDF from previous node)

This wrapper:
  1. Reads the PDF from stdin (base64) or from a file path argument
  2. Writes it to a temp file
  3. Runs the extractor
  4. Returns clean JSON for n8n to parse
"""

import sys
import json
import base64
import tempfile
import os
from pathlib import Path

# Import the extractor (must be in the same directory)
sys.path.insert(0, str(Path(__file__).parent))
from adobe_sign_extractor import extract


def main():
    # n8n sends binary data as base64 via stdin
    raw_input = sys.stdin.buffer.read()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
        try:
            # Try to decode as base64 first (n8n binary node output)
            decoded = base64.b64decode(raw_input)
            tmp.write(decoded)
        except Exception:
            # If it's already raw bytes (direct pipe), write as-is
            tmp.write(raw_input)

    try:
        result = extract(tmp_path, debug=False)
        print(json.dumps(result, default=str, ensure_ascii=False))
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()


# =============================================================================
# n8n WORKFLOW NOTES
# =============================================================================
#
# RECOMMENDED NODE SEQUENCE:
#
#  [Trigger]
#    ↓  (Google Drive / Email / Webhook — returns binary PDF)
#  [Execute Command]
#    Command: python3 /opt/scripts/n8n_wrapper.py
#    Stdin:   {{ $binary.data }}
#    ↓
#  [Code Node — parse JSON]
#    return JSON.parse($input.first().json.stdout);
#    ↓
#  [Switch Node — route by doc_type]
#    Condition 1: {{ $json.doc_type }} == "PO_STANDARD"
#    Condition 2: {{ $json.doc_type }} == "PO_CAPEX"
#    Condition 3: {{ $json.doc_type }} == "PO_SERVICE"
#    Condition 4: {{ $json.doc_type }} == "PO_EMERGENCY"
#    ↓ (per branch)
#  [Set Node — build row array for Sheets]
#    Values:
#      Vendor Name   → {{ $json.data["Vendor Name"] }}
#      PO Number     → {{ $json.data["PO Number"] }}
#      Signed At     → {{ $json.timestamps.signed_timestamp }}
#      Completed At  → {{ $json.timestamps.completed_timestamp }}
#      ... etc
#    ↓
#  [Google Sheets — Append Row]
#    Sheet: "PO Tracker"
#    Tab:   PO_STANDARD  (use one tab per doc type, or one shared tab)
#
# =============================================================================
#
# GOOGLE SHEETS COLUMN LAYOUT (suggested — one sheet per doc type)
#
# Tab: PO_STANDARD
# | A          | B         | C          | D          | E           | F           |
# | PO Number  | Vendor    | Department | Amount     | Signed At   | Completed   |
#
# Tab: PO_CAPEX
# | A          | B         | C            | D          | E           | F           |
# | PO Number  | Vendor    | Project Code | Amount     | Signed At   | Completed   |
#
# ... and so on for the other 2 tabs.
#
# =============================================================================
