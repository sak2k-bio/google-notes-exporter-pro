import os
import sys
import argparse
import json
from pathlib import Path
from typing import List
from fpdf import FPDF

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def safe_fname(name: str) -> str:
    return ''.join(c for c in (name or "Untitled") if c.isalnum() or c in (' ', '-', '_')).rstrip() or "note"


essential_json_keys = (
    "title", "textContent", "labels", "attachments"
)


def load_note_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Some Takeout exports use "userEditedTimestampUsec" etc.; not strictly required here.
            return data
    except Exception as e:
        print(f"[Warning] Failed to load JSON {path}: {e}")
        return {}


def derive_attachment_paths(note_json: dict, keep_dir: Path, takeout_root: Path) -> List[Path]:
    paths: List[Path] = []
    atts = note_json.get("attachments", []) or []
    for att in atts:
        fp = att.get("filePath") or att.get("file_path")
        if not fp:
            continue
        p = Path(fp)
        if p.is_absolute():
            candidate = p
        else:
            # filePath often starts with "Keep/"; join from Takeout root
            if str(p).startswith("Keep" + os.sep) or str(p).startswith("Keep/"):
                candidate = takeout_root / p
            else:
                candidate = keep_dir / p
        if candidate.exists():
            paths.append(candidate)
    return paths


def find_sibling_attachments(json_file: Path) -> List[Path]:
    # Fallback: look for files sharing the same stem as the JSON basename
    stem = json_file.stem
    attachments = []
    for item in json_file.parent.iterdir():
        if item.is_file() and item.suffix.lower() in IMAGE_EXTS and item.stem.startswith(stem):
            attachments.append(item)
    return attachments


def export_takeout_keep_to_pdfs(source: Path, out_dir: Path) -> None:
    keep_dir = source
    takeout_root = keep_dir.parent  # Typically .../Takeout
    out_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(keep_dir.rglob("*.json"))
    if not json_files:
        print(f"No JSON files found under {keep_dir}. Make sure you pointed to the Keep/ folder from Google Takeout.")
        return

    total = 0
    for jf in json_files:
        note = load_note_json(jf)
        if not note:
            continue

        title = note.get("title") or "Untitled"
        text = note.get("textContent") or note.get("text", "")
        labels = [l.get("name") for l in (note.get("labels") or []) if isinstance(l, dict) and l.get("name")] or ["Unlabeled"]

        # Attachments
        att_paths = derive_attachment_paths(note, keep_dir=keep_dir, takeout_root=takeout_root)
        if not att_paths:
            att_paths = find_sibling_attachments(jf)

        for label in labels:
            label_folder = out_dir / safe_fname(label)
            label_folder.mkdir(parents=True, exist_ok=True)

            pdf_name = f"{safe_fname(title)}.pdf"
            pdf_path = label_folder / pdf_name

            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=16)
            pdf.cell(0, 12, title, ln=True)
            pdf.set_font("Arial", size=12)
            if text:
                pdf.multi_cell(0, 10, text, align='L')
                pdf.ln(2)

            for img in att_paths:
                try:
                    pdf.image(str(img), w=120)
                    pdf.ln(5)
                except Exception as e:
                    print(f"[Warning] Could not embed image '{img}': {e}")

            try:
                pdf.output(str(pdf_path), 'F')
                total += 1
            except Exception as e:
                print(f"[Warning] Failed to write PDF '{pdf_path}': {e}")

    print(f"Export complete. Wrote {total} PDF(s) to '{out_dir}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Google Takeout Keep folder into PDFs grouped by labels.")
    parser.add_argument("--source", "-s", type=str, default=str(Path("Takeout") / "Keep"), help="Path to the Keep/ directory from Takeout")
    parser.add_argument("--out", "-o", type=str, default="exported_notes_pdf_takeout", help="Output directory for PDFs")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()

    if not source.exists() or not source.is_dir():
        print(f"Source directory not found: {source}")
        sys.exit(1)

    export_takeout_keep_to_pdfs(source, out_dir)
