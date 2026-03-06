"""
adobe_sign_extractor.py
-----------------------
Extracts AcroForm field values AND Adobe Sign timestamps from signed PDF files.
Designed to run inside an n8n "Execute Command" node or as a standalone script.

Usage:
    python adobe_sign_extractor.py <path_to_pdf>
    python adobe_sign_extractor.py <path_to_pdf> --debug

Output:
    JSON printed to stdout — ready to be consumed by n8n's next node.

Dependencies:
    pip install pypdf pdfplumber

Author: IT Architect template — customise DOC_TYPE_CONFIGS for your 4 document types.
"""

import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIGURATION — Edit this section to match your 4 document types
# ---------------------------------------------------------------------------

# Each document type is identified by a "discriminator": a field name whose
# value (or the document title) uniquely identifies that doc type.
# Then we declare which AcroForm field names map to which output column names.

DOC_TYPE_CONFIGS = {

    "PO_STANDARD": {
        # How to detect this doc type:
        #   "field" means look at an AcroForm field value
        #   "title" means look at the PDF title metadata
        "discriminator_field": "doc_type",          # AcroForm field name
        "discriminator_value": "Standard PO",       # expected value
        # Field mapping: { acroform_field_name : output_column_name }
        "fields": {
            "vendor_name":        "Vendor Name",
            "vendor_id":          "Vendor ID",
            "po_number":          "PO Number",
            "po_date":            "PO Date",
            "department":         "Department",
            "cost_center":        "Cost Center",
            "total_amount":       "Total Amount",
            "currency":           "Currency",
            "requestor_name":     "Requestor",
            "approver_name":      "Approver",
            "description":        "Description",
            "notes":              "Notes",
        }
    },

    "PO_CAPEX": {
        "discriminator_field": "doc_type",
        "discriminator_value": "CapEx PO",
        "fields": {
            "vendor_name":        "Vendor Name",
            "vendor_id":          "Vendor ID",
            "po_number":          "PO Number",
            "po_date":            "PO Date",
            "project_code":       "Project Code",
            "asset_category":     "Asset Category",
            "total_amount":       "Total Amount",
            "currency":           "Currency",
            "budget_line":        "Budget Line",
            "requestor_name":     "Requestor",
            "approver_name":      "Approver",
            "cfo_approver":       "CFO Approver",
            "description":        "Description",
        }
    },

    "PO_SERVICE": {
        "discriminator_field": "doc_type",
        "discriminator_value": "Service PO",
        "fields": {
            "vendor_name":        "Vendor Name",
            "service_type":       "Service Type",
            "po_number":          "PO Number",
            "po_date":            "PO Date",
            "start_date":         "Service Start Date",
            "end_date":           "Service End Date",
            "total_amount":       "Total Amount",
            "currency":           "Currency",
            "requestor_name":     "Requestor",
            "approver_name":      "Approver",
            "contract_ref":       "Contract Reference",
        }
    },

    "PO_EMERGENCY": {
        "discriminator_field": "doc_type",
        "discriminator_value": "Emergency PO",
        "fields": {
            "vendor_name":        "Vendor Name",
            "po_number":          "PO Number",
            "po_date":            "PO Date",
            "justification":      "Justification",
            "total_amount":       "Total Amount",
            "currency":           "Currency",
            "requestor_name":     "Requestor",
            "approver_name":      "Approver",
            "emergency_level":    "Emergency Level",
        }
    },
}

# If you prefer to discriminate by PDF title metadata instead of a field value,
# use this dictionary: { substring_in_title : doc_type_key }
TITLE_DISCRIMINATORS = {
    "Standard Purchase Order":  "PO_STANDARD",
    "Capital Expenditure":      "PO_CAPEX",
    "Service Purchase Order":   "PO_SERVICE",
    "Emergency Purchase":       "PO_EMERGENCY",
}


# ---------------------------------------------------------------------------
# STEP 1 — Extract ALL AcroForm fields from the PDF
# ---------------------------------------------------------------------------

def extract_acroform_fields(pdf_path: str, debug: bool = False) -> dict:
    """
    Returns a flat dict of { field_name: field_value } for every AcroForm
    field present in the PDF, regardless of type (text, checkbox, radio, etc.)
    Uses pypdf which handles AcroForm natively.
    """
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    fields = {}

    if reader.get_fields() is None:
        if debug:
            print("[DEBUG] No AcroForm fields found via pypdf", file=sys.stderr)
        return fields

    raw_fields = reader.get_fields()

    for name, field_obj in raw_fields.items():
        value = field_obj.value
        # Normalise: strip whitespace, convert None to ""
        if value is None:
            value = ""
        elif isinstance(value, bool):
            value = str(value)
        else:
            value = str(value).strip()
        fields[name] = value

    if debug:
        print(f"[DEBUG] AcroForm fields found ({len(fields)}):", file=sys.stderr)
        for k, v in fields.items():
            print(f"  {k!r} = {v!r}", file=sys.stderr)

    return fields


# ---------------------------------------------------------------------------
# STEP 2 — Extract Adobe Sign timestamps from XMP metadata
# ---------------------------------------------------------------------------

def extract_xmp_timestamps(pdf_path: str, debug: bool = False) -> dict:
    """
    Adobe Sign embeds an XML audit trail in the PDF's XMP metadata stream.
    We parse it with regex (no external XML lib needed for this structure).

    Returns a dict with keys like:
        sent_timestamp, viewed_timestamp, signed_timestamp, completed_timestamp
    All values are ISO-8601 strings or "" if not found.
    """
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    timestamps = {}

    # XMP lives in the document's metadata stream
    try:
        xmp = reader.xmp_metadata
        if xmp is None:
            if debug:
                print("[DEBUG] No XMP metadata object found", file=sys.stderr)
            return timestamps

        # Serialise the XMP object to a string we can search
        xmp_str = str(xmp)

        if debug:
            print(f"[DEBUG] XMP metadata length: {len(xmp_str)} chars", file=sys.stderr)
            # Print first 2000 chars so you can see what's there
            print(f"[DEBUG] XMP snippet:\n{xmp_str[:2000]}", file=sys.stderr)

        timestamps.update(_parse_adobe_sign_xmp(xmp_str, debug))

    except Exception as e:
        if debug:
            print(f"[DEBUG] XMP extraction error: {e}", file=sys.stderr)

    return timestamps


def _parse_adobe_sign_xmp(xmp_str: str, debug: bool = False) -> dict:
    """
    Parses Adobe Sign-specific XMP fields.
    Adobe Sign uses the 'echosign' or 'adobesign' XMP namespace.
    Common field names (adjust if your version differs):
        echosign:DateSent, echosign:DateSigned, echosign:DateCompleted
        adobesign:* variants
    """
    result = {}

    # Patterns cover both namespace prefixes Adobe has used over the years
    patterns = {
        "sent_timestamp":      r'(?:echosign|adobesign):DateSent[^>]*>([^<]+)<',
        "signed_timestamp":    r'(?:echosign|adobesign):DateSigned[^>]*>([^<]+)<',
        "completed_timestamp": r'(?:echosign|adobesign):DateCompleted[^>]*>([^<]+)<',
        "viewed_timestamp":    r'(?:echosign|adobesign):DateViewed[^>]*>([^<]+)<',
        "created_timestamp":   r'(?:echosign|adobesign):DateCreated[^>]*>([^<]+)<',
        # Standard XMP dates — always present
        "pdf_created":         r'xmp:CreateDate[^>]*>([^<]+)<',
        "pdf_modified":        r'xmp:ModifyDate[^>]*>([^<]+)<',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, xmp_str, re.IGNORECASE)
        if match:
            raw_ts = match.group(1).strip()
            result[key] = _normalise_timestamp(raw_ts)
            if debug:
                print(f"[DEBUG] Timestamp {key}: {raw_ts} → {result[key]}", file=sys.stderr)
        else:
            result[key] = ""

    return result


def _normalise_timestamp(raw: str) -> str:
    """
    Converts various timestamp formats to ISO-8601.
    Adobe Sign uses formats like:
        2024-03-15T14:32:00Z
        2024-03-15T14:32:00+00:00
        D:20240315143200Z  (PDF date format)
    """
    raw = raw.strip()
    if not raw:
        return ""

    # PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
    pdf_date_match = re.match(
        r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", raw
    )
    if pdf_date_match:
        y, mo, d, h, mi, s = pdf_date_match.groups()
        return f"{y}-{mo}-{d}T{h}:{mi}:{s}Z"

    # Already ISO-8601 — return as-is
    if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", raw):
        return raw

    return raw  # Return whatever we found, unchanged


# ---------------------------------------------------------------------------
# STEP 3 — Extract timestamps from the Adobe Sign Audit Trail page (fallback)
# ---------------------------------------------------------------------------

def extract_audit_trail_timestamps(pdf_path: str, debug: bool = False) -> dict:
    """
    Adobe Sign appends a visual 'Audit Trail' page at the end of the PDF.
    This function extracts timestamps from that page's text as a fallback
    when XMP metadata doesn't contain them.

    The audit trail page typically looks like:
        Sent for signature to John Smith (john@example.com)
        2024-03-15 | 14:32:00 UTC

        Viewed by John Smith (john@example.com)
        2024-03-15 | 14:35:00 UTC

        Signed by John Smith (john@example.com)
        2024-03-15 | 14:36:00 UTC

        Document completed.
        2024-03-15 | 14:36:00 UTC
    """
    import pdfplumber

    result = {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Audit trail is always the last page
            last_page = pdf.pages[-1]
            text = last_page.extract_text() or ""

            if debug:
                print(f"[DEBUG] Last page text (audit trail candidate):\n{text[:1500]}", file=sys.stderr)

            # Detect if this really is an audit trail page
            is_audit_page = any(
                marker in text
                for marker in ["Audit Trail", "audit trail", "Adobe Sign", "EchoSign",
                               "Sent for signature", "Document completed"]
            )

            if not is_audit_page:
                if debug:
                    print("[DEBUG] Last page does not appear to be an audit trail", file=sys.stderr)
                return result

            result["audit_trail_raw_text"] = text

            # Extract structured events: look for action lines followed by timestamps
            # Timestamp patterns: YYYY-MM-DD | HH:MM:SS UTC  or  MM/DD/YYYY HH:MM:SS AM/PM
            ts_pattern = re.compile(
                r"(\d{4}-\d{2}-\d{2}\s*[|]\s*\d{2}:\d{2}:\d{2}(?:\s*UTC)?)"
                r"|(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?(?:\s+\w+)?)"
            )

            # Action keyword mapping
            action_map = {
                "sent":       ["sent for signature", "sent to"],
                "viewed":     ["viewed by", "opened by"],
                "signed":     ["signed by", "digitally signed"],
                "completed":  ["document completed", "completed", "agreement completed"],
                "delegated":  ["delegated to"],
                "declined":   ["declined by"],
            }

            lines = text.split("\n")
            current_action = None

            for line in lines:
                line_lower = line.lower().strip()

                # Detect action
                for action, keywords in action_map.items():
                    if any(kw in line_lower for kw in keywords):
                        current_action = action
                        break

                # Detect timestamp on this line
                ts_match = ts_pattern.search(line)
                if ts_match and current_action:
                    raw_ts = (ts_match.group(1) or ts_match.group(2)).strip()
                    key = f"{current_action}_timestamp"
                    # Keep the first occurrence of each action type
                    if key not in result:
                        result[key] = _normalise_audit_timestamp(raw_ts)
                        if debug:
                            print(f"[DEBUG] Audit trail event: {key} = {result[key]}", file=sys.stderr)
                    current_action = None  # reset after capturing

    except Exception as e:
        if debug:
            print(f"[DEBUG] Audit trail extraction error: {e}", file=sys.stderr)

    return result


def _normalise_audit_timestamp(raw: str) -> str:
    """Normalise audit trail timestamps to ISO-8601."""
    raw = raw.strip()

    # Format: 2024-03-15 | 14:32:00 UTC
    m = re.match(r"(\d{4}-\d{2}-\d{2})\s*[|]\s*(\d{2}:\d{2}:\d{2})", raw)
    if m:
        return f"{m.group(1)}T{m.group(2)}Z"

    # Format: 03/15/2024 02:32:00 PM UTC
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}:\d{2}:\d{2})\s*(AM|PM)?", raw)
    if m:
        mo, d, y, time_part, ampm = m.groups()
        if ampm:
            # Convert 12h to 24h
            h, mi, s = time_part.split(":")
            h = int(h)
            if ampm == "PM" and h != 12:
                h += 12
            elif ampm == "AM" and h == 12:
                h = 0
            time_part = f"{h:02d}:{mi}:{s}"
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}T{time_part}Z"

    return raw


# ---------------------------------------------------------------------------
# STEP 4 — Extract PDF standard metadata (creation date, author, title)
# ---------------------------------------------------------------------------

def extract_pdf_metadata(pdf_path: str, debug: bool = False) -> dict:
    """Extracts standard PDF document info dictionary fields."""
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    meta = reader.metadata or {}

    result = {
        "pdf_title":    str(meta.get("/Title", "") or "").strip(),
        "pdf_author":   str(meta.get("/Author", "") or "").strip(),
        "pdf_subject":  str(meta.get("/Subject", "") or "").strip(),
        "pdf_creator":  str(meta.get("/Creator", "") or "").strip(),
        "pdf_producer": str(meta.get("/Producer", "") or "").strip(),
        "pdf_creation_date": _normalise_timestamp(str(meta.get("/CreationDate", "") or "")),
        "pdf_mod_date":      _normalise_timestamp(str(meta.get("/ModDate", "") or "")),
        "page_count":   len(reader.pages),
    }

    if debug:
        print(f"[DEBUG] PDF metadata: {json.dumps(result, indent=2)}", file=sys.stderr)

    return result


# ---------------------------------------------------------------------------
# STEP 5 — Identify document type
# ---------------------------------------------------------------------------

def identify_doc_type(fields: dict, pdf_meta: dict, debug: bool = False) -> str:
    """
    Tries to identify which of the 4 document types this PDF is.
    Strategy:
      1. Check the AcroForm discriminator field value
      2. Fall back to PDF title metadata keyword matching
      3. Return "UNKNOWN" if neither matches
    """
    # Strategy 1: AcroForm field
    for doc_type, config in DOC_TYPE_CONFIGS.items():
        disc_field = config.get("discriminator_field")
        disc_value = config.get("discriminator_value", "").lower()
        if disc_field and disc_field in fields:
            if fields[disc_field].lower() == disc_value:
                if debug:
                    print(f"[DEBUG] Doc type identified by field: {doc_type}", file=sys.stderr)
                return doc_type

    # Strategy 2: PDF title
    title = pdf_meta.get("pdf_title", "").lower()
    for title_fragment, doc_type in TITLE_DISCRIMINATORS.items():
        if title_fragment.lower() in title:
            if debug:
                print(f"[DEBUG] Doc type identified by title: {doc_type}", file=sys.stderr)
            return doc_type

    if debug:
        print(f"[DEBUG] Doc type UNKNOWN. Fields: {list(fields.keys())}", file=sys.stderr)
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# STEP 6 — Map raw fields to output columns based on doc type config
# ---------------------------------------------------------------------------

def map_fields_to_output(doc_type: str, fields: dict, debug: bool = False) -> dict:
    """
    Applies the field mapping from DOC_TYPE_CONFIGS to produce the final
    output dict with human-readable column names as keys.
    Also includes any unmapped fields under "extra_fields" for debugging.
    """
    if doc_type not in DOC_TYPE_CONFIGS:
        # Unknown doc — return all raw fields as-is
        return {"raw_fields": fields}

    config = DOC_TYPE_CONFIGS[doc_type]
    field_map = config.get("fields", {})

    output = {}
    mapped_source_fields = set()

    for source_field, output_column in field_map.items():
        value = fields.get(source_field, "")
        output[output_column] = value
        mapped_source_fields.add(source_field)

    # Capture any fields present in the PDF but not in our mapping
    extra = {k: v for k, v in fields.items() if k not in mapped_source_fields and v}
    if extra:
        output["_extra_fields"] = extra

    return output


# ---------------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------------

def extract(pdf_path: str, debug: bool = False) -> dict:
    """
    Full extraction pipeline. Returns a JSON-serialisable dict ready for n8n.
    """
    pdf_path = str(Path(pdf_path).resolve())

    result = {
        "source_file": pdf_path,
        "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
        "doc_type": "UNKNOWN",
        "status": "ok",
        "errors": [],
    }

    # --- 1. PDF metadata
    try:
        pdf_meta = extract_pdf_metadata(pdf_path, debug)
        result["pdf_metadata"] = pdf_meta
    except Exception as e:
        result["errors"].append(f"pdf_metadata: {e}")
        pdf_meta = {}

    # --- 2. AcroForm fields
    try:
        fields = extract_acroform_fields(pdf_path, debug)
        result["raw_acroform_fields"] = fields
    except Exception as e:
        result["errors"].append(f"acroform: {e}")
        fields = {}

    # --- 3. Identify doc type
    doc_type = identify_doc_type(fields, pdf_meta, debug)
    result["doc_type"] = doc_type

    # --- 4. Map to output columns
    result["data"] = map_fields_to_output(doc_type, fields, debug)

    # --- 5. XMP timestamps
    try:
        xmp_ts = extract_xmp_timestamps(pdf_path, debug)
        result["timestamps_xmp"] = xmp_ts
    except Exception as e:
        result["errors"].append(f"xmp_timestamps: {e}")
        xmp_ts = {}

    # --- 6. Audit trail timestamps (fallback / supplement)
    try:
        audit_ts = extract_audit_trail_timestamps(pdf_path, debug)
        result["timestamps_audit_trail"] = audit_ts
    except Exception as e:
        result["errors"].append(f"audit_trail: {e}")
        audit_ts = {}

    # --- 7. Build a consolidated timestamps block (XMP wins, audit trail fills gaps)
    consolidated = {}
    for key in ["sent_timestamp", "viewed_timestamp", "signed_timestamp",
                "completed_timestamp", "created_timestamp"]:
        consolidated[key] = (
            xmp_ts.get(key)
            or audit_ts.get(key)
            or pdf_meta.get("pdf_creation_date" if "created" in key else "pdf_mod_date", "")
            or ""
        )
    result["timestamps"] = consolidated

    if result["errors"]:
        result["status"] = "partial"

    return result


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract AcroForm fields and Adobe Sign timestamps from a signed PDF."
    )
    parser.add_argument("pdf_path", help="Path to the signed PDF file")
    parser.add_argument(
        "--debug", action="store_true",
        help="Print debug information to stderr (safe for n8n — stdout stays clean JSON)"
    )
    parser.add_argument(
        "--pretty", action="store_true",
        help="Pretty-print JSON output (use for manual inspection)"
    )
    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        error = {"status": "error", "message": f"File not found: {args.pdf_path}"}
        print(json.dumps(error))
        sys.exit(1)

    output = extract(args.pdf_path, debug=args.debug)

    indent = 2 if args.pretty else None
    print(json.dumps(output, indent=indent, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()