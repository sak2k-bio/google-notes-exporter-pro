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

# --- PDF Generation ---
for note in keep.all():
    labels = [lbl.name for lbl in note.labels.all()] if getattr(note, 'labels', None) else ['Unlabeled']
    for label in labels:
        folder = os.path.join(export_base, label)
        os.makedirs(folder, exist_ok=True)

        title = getattr(note, 'title', '') or 'Untitled'
        text = getattr(note, 'text', '') or ''

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
