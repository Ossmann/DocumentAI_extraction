import fitz  # PyMuPDF

# Open the PDF file
pdf_document = "Group_Rates_small.pdf"
doc = fitz.open(pdf_document)

# Extract text from each page and convert to markdown
md_text = ""
for page_num in range(len(doc)):
    page = doc.load_page(page_num)
    md_text += page.get_text("markdown")  # Extracts text as markdown

# Print the extracted markdown text
print(md_text)