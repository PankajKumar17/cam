import PyPDF2
reader = PyPDF2.PdfReader('India Innovates 2026.pdf')
text = [p.extract_text() for p in reader.pages]
with open('pdf_content.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(text))
