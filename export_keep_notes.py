import os
import json
import gkeepapi
from fpdf import FPDF

# --- Load credentials ---
with open('account.json', 'r', encoding='utf-8') as f:
    account = json.load(f)

keep = gkeepapi.Keep()
try:
    # Authenticate with Google Keep (use an App Password if 2FA is enabled)
    # You can optionally provide a stable Android-like device ID in account.json as "DeviceId": "android-<16hex>"
    device_id = account.get('DeviceId')
    if device_id:
        keep.authenticate(account['UserName'], account['Password'], device_id=device_id)
    else:
        keep.authenticate(account['UserName'], account['Password'])
    # Fetch latest notes and labels
    keep.sync()
except Exception as e:
    print(
        "Authentication failed. Create a Google App Password and ensure access via DisplayUnlockCaptcha, "
        "then try again."
    )
    print(f"Details: {e}")
    raise SystemExit(1)

# --- Export Setup ---
export_base = 'exported_notes_pdf'
os.makedirs(export_base, exist_ok=True)

def safe_fname(name: str) -> str:
    return ''.join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip() or "note"


def clean_text_for_pdf(text: str) -> str:
    """Remove or replace characters that can't be encoded in latin-1 for FPDF."""
    if not text:
        return text
    
    # Try to encode to latin-1, replace problematic characters
    try:
        text.encode('latin-1')
        return text
    except UnicodeEncodeError:
        # Replace common Unicode characters with ASCII equivalents
        replacements = {
            '\u2019': "'",  # Right single quotation mark
            '\u201c': '"',  # Left double quotation mark
            '\u201d': '"',  # Right double quotation mark
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u2026': '...',  # Horizontal ellipsis
        }
        
        for unicode_char, replacement in replacements.items():
            text = text.replace(unicode_char, replacement)
        
        # Remove any remaining characters that can't be encoded in latin-1
        text = text.encode('latin-1', errors='ignore').decode('latin-1')
        
        return text

# --- PDF Generation ---
for note in keep.all():
    labels = [lbl.name for lbl in note.labels.all()] if getattr(note, 'labels', None) else ['Unlabeled']
    for label in labels:
        folder = os.path.join(export_base, label)
        os.makedirs(folder, exist_ok=True)

        title = clean_text_for_pdf(getattr(note, 'title', '') or 'Untitled')
        text = clean_text_for_pdf(getattr(note, 'text', '') or '')

        pdf_name = f"{safe_fname(title)}.pdf"
        pdf_path = os.path.join(folder, pdf_name)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=16)
        pdf.cell(0, 12, title, ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, text, align='L')
        pdf.ln(2)

        # Attach and insert images inline
        for idx, attachment in enumerate(getattr(note, 'attachments', []) or []):
            ext = getattr(attachment, 'mimetype', 'jpg').split('/')[-1]
            img_fname = f"{safe_fname(title)}_{idx}.{ext}"
            img_path = os.path.join(folder, img_fname)
            try:
                with open(img_path, 'wb') as img_file:
                    img_file.write(getattr(attachment, 'blob', b''))
                if os.path.getsize(img_path) > 0:
                    pdf.image(img_path, w=80)
                    pdf.ln(5)
                else:
                    os.remove(img_path)
            except Exception as e:
                print(f"[Warning] Error saving image attachment for {title}: {e}")

        pdf.output(pdf_path, 'F')

print("PDF export finished. Check 'exported_notes_pdf' folder.")
