import fitz  # For PyMuPDF, though the modern usage is just 'import fitz'
from matplotlib import pyplot as plt
from pandas import DataFrame, Series  # Importing specific classes from pandas
from numpy import array, random 


######### Get PDF text and tables as markup #################
# Create a document object
doc = fitz.open('Group_Rates_small.pdf')

# Extract the number of pages (int)
print(doc.page_count)
page_count = doc.page_count

# Loop through each page by index
for i in range(page_count):
    # Get the page by index
    page = doc.load_page(i)   

    # Convert the TableFinder object to a list
    tabs = list(page.find_tables())  # detect the tables and convert to list

    # Collect the bounding boxes of all cells in all tables
    table_areas = []
    for tab in tabs:
        for cell in tab.cells:
            table_areas.append(cell[:4])  # Each cell has a bounding box defined by (x0, y0, x1, y1)

    # Extract and print each table's content
    for i, tab in enumerate(tabs):  # iterate over all tables
        table_data = tab.extract()
        for row_index, row_content in enumerate(table_data):
            print(f"Row {row_index}: {row_content}")
    
    # get all the text
    all_text = page.get_text("markdown")
    
    # Remove text that falls within the bounding boxes of the table cells to avoid duplicate
    for area in table_areas:
        clip_rect = fitz.Rect(area)
        non_table_text = all_text.replace(page.get_text("markdown", clip=clip_rect), "")
    
    # Print the non-table text
    print(f"Text on page {i + 1}:\n{non_table_text}\n")