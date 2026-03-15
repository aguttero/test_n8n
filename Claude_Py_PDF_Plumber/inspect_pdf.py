"""
inspect_pdf.py
--------------
Run this ONCE on each of your 4 PDF document types to discover:
  - All AcroForm field names and their current values
  - PDF metadata (title, author, creator)
  - XMP metadata snippet (so you can find Adobe Sign timestamp field names)
  - Last page text (audit trail)

Use the output of this script to fill in the DOC_TYPE_CONFIGS in
adobe_sign_extractor.py with the REAL field names from your documents.

Usage:
    python3 inspect_pdf.py path/to/your_signed_po.pdf
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from adobe_sign_extractor import (
    extract_acroform_fields,
    extract_pdf_metadata,
    extract_xmp_timestamps,
    extract_audit_trail_timestamps,
)


def inspect(pdf_path: str):
    print("=" * 70)
    print(f"PDF INSPECTION REPORT: {pdf_path}")
    print("=" * 70)

    # 1. Standard metadata
    print("\n── PDF METADATA ──────────────────────────────────────────────────")
    meta = extract_pdf_metadata(pdf_path, debug=False)
    for k, v in meta.items():
        print(f"  {k:<25} {v}")

    # 2. All AcroForm fields
    print("\n── ACROFORM FIELDS ────────────────────────────────────────────────")
    fields = extract_acroform_fields(pdf_path, debug=False)
    if not fields:
        print("  ⚠  No AcroForm fields found.")
        print("     The form data may be flattened or the fields may be in XFA format.")
    else:
        print(f"  Total fields: {len(fields)}\n")
        for name, value in sorted(fields.items()):
            display_val = repr(value) if value else "(empty)"
            print(f"  [{name}]")
            print(f"    value = {display_val}")

    # 3. XMP timestamps
    print("\n── XMP / ADOBE SIGN TIMESTAMPS ────────────────────────────────────")
    xmp = extract_xmp_timestamps(pdf_path, debug=True)  # debug=True prints the raw XMP
    for k, v in xmp.items():
        print(f"  {k:<30} {v or '(not found)'}")

    # 4. Audit trail page
    print("\n── AUDIT TRAIL (last page text) ───────────────────────────────────")
    audit = extract_audit_trail_timestamps(pdf_path, debug=False)
    if "audit_trail_raw_text" in audit:
        print(audit["audit_trail_raw_text"])
        print("\n  Parsed events:")
        for k, v in audit.items():
            if k != "audit_trail_raw_text":
                print(f"  {k:<30} {v}")
    else:
        print("  No audit trail page detected.")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("  1. Copy the AcroForm field names above into DOC_TYPE_CONFIGS")
    print("     in adobe_sign_extractor.py")
    print("  2. Set the discriminator_field and discriminator_value to")
    print("     whatever uniquely identifies this doc type")
    print("  3. If XMP timestamps are empty, check the raw XMP snippet above")
    print("     and update the regex patterns in _parse_adobe_sign_xmp()")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 inspect_pdf.py <path_to_pdf>")
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)

    inspect(path)
