<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# now give me the complete code with readme

Below is a complete solution: a Python script that authenticates to Google Keep, exports all labeled notes and their images as PDFs (with images embedded in the notes), and a README for setup and usage. This combines gkeepapi and FPDF for seamless offline archiving of Keep notes by label[^1][^2][^3].

***

# README: Google Keep PDF Exporter

## Overview

Export all Google Keep notes as PDFs with images embedded, sorted into folders named after each note’s label.

***

## Prerequisites

- Python 3.7+
- Required packages:

```
pip install gkeepapi fpdf
```


***

## Credentials Setup

1. **Create a Google App Password** for enhanced security ([see guide][^1]).
2. **Create an `account.json` file** in your working directory:
```json
{
  "UserName": "your_google_email@gmail.com",
  "Password": "your_google_app_password"
}
```


***

## Running the Script

1. Save the following code as `export_keep_notes.py`.
2. Ensure your `account.json` is present.
3. Run:

```
python export_keep_notes.py
```


## Export Structure

- Each label gets its own folder (under `exported_notes_pdf/`).
- Each note is a PDF file with its text and any attached images included inline.
***

# Complete Python Script

```python
import os
import gkeepapi
import json
from fpdf import FPDF

# --- Load credentials ---
with open('account.json', 'r', encoding='utf-8') as f:
    account = json.load(f)

keep = gkeepapi.Keep()
if not keep.login(account['UserName'], account['Password']):
    print("Login failed. Try creating an app password and use it instead.")
    exit()

# --- Export Setup ---
export_base = 'exported_notes_pdf'
os.makedirs(export_base, exist_ok=True)

def safe_fname(name):
    return ''.join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip() or "note"

# --- PDF Generation ---
for note in keep.all():
    labels = [lbl.name for lbl in note.labels.all()] if note.labels else ['Unlabeled']
    for label in labels:
        folder = os.path.join(export_base, label)
        os.makedirs(folder, exist_ok=True)

        pdf_name = f"{safe_fname(note.title)}.pdf"
        pdf_path = os.path.join(folder, pdf_name)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=16)
        pdf.cell(0, 12, note.title, ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, note.text, align='L')
        pdf.ln(2)

        # Attach and insert images inline
        for idx, attachment in enumerate(getattr(note, "attachments", [])):
            ext = getattr(attachment, 'mimetype', 'jpg').split('/')[-1]
            img_fname = f"{safe_fname(note.title)}_{idx}.{ext}"
            img_path = os.path.join(folder, img_fname)
            try:
                with open(img_path, "wb") as img_file:
                    img_file.write(attachment.blob)
                pdf.image(img_path, w=80)
                pdf.ln(5)
            except Exception as e:
                print(f"[Warning] Error saving image attachment for {note.title}: {e}")

        pdf.output(pdf_path, "F")
print("PDF export finished. Check 'exported_notes_pdf' folder.")
```


***

## Troubleshooting

- If authentication fails, visit [DisplayUnlockCaptcha](https://accounts.google.com/DisplayUnlockCaptcha) and permit access[^1].
- Image issues: Make sure gkeepapi is up-to-date. Attachments are fetched via `note.attachments`[^2][^3].
- PDF formatting: This exports simple layouts, but FPDF can be customized if you want richer formatting.

***

## References

- [gkeepapi documentation][^1]
- [FPDF documentation][^2][^3]

***

This README and script enable organized, bulk archival of Google Keep notes and their images into local PDF files with robust structure and easy setup.

<div style="text-align: center">⁂</div>

[^1]: https://clay-atlas.com/us/blog/2020/12/17/python-en-google-keep-gkeepapi/

[^2]: https://www.youtube.com/watch?v=dQshrfd5Lpk

[^3]: https://roytuts.com/python-add-images-to-pdf-documents/

