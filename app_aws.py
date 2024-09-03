
import fitz
import boto3
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import multiprocessing
import os
import csv
import json

# load the OpenAI API Key from environment variables
load_dotenv()

# Initialize S3 client
s3_client = boto3.client('s3')

######### 1. Download PDF from S3 #################
def download_pdf_from_s3(bucket_name, s3_key, local_file_path):
    s3_client.download_file(bucket_name, s3_key, local_file_path)

######### 2. Get PDF text and tables as markup #################
def extract_text_tables_pdf(file_path):
    # Create a document object
    doc = fitz.open(file_path)

    # Initialize an empty string to hold the entire extracted markup text from the pdf
    pdf_markup = ""

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

        # initialize the varible that holds the text where duplicate tables have been removed
        non_table_text = ""
        
        # Remove text that falls within the bounding boxes of the table cells to avoid duplicate
        for area in table_areas:
            clip_rect = fitz.Rect(area)
            non_table_text = all_text.replace(page.get_text("markdown", clip=clip_rect), "")
        
        # Add the non-table text to the markup
        pdf_markup += f"Text on page {i + 1}:\n{non_table_text}\n"

    # Return the accumulated markup
    return pdf_markup
    

######### 3. Extract structured info from text via LLM #################

def extract_structured_data(content: str, data_points):

    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo") #Set the LLM model and give it instructions message
    template = """
    You are an expert admin people who will extract core information from documents

    {content}

    Above is the content; please try to extract all data points from the content above 
    and export in a JSON array format:
    {data_points}

    Now please extract details from the content  and export in a JSON array format, 
    return ONLY the JSON array:
    """

    #create the prompt template to pass on content and data points to the LLM
    prompt = PromptTemplate(
        input_variables=["content", "data_points"],
        template=template,
    )

    # Prepare the input dictionary for the invoke method
    input_data = {
        "content": content,
        "data_points": data_points
    }


    # Chain the prompt and model together using RunnableSequence
    chain = prompt | llm | StrOutputParser()


    # chain = LLMChain(llm=llm, prompt=prompt)
    results = chain.invoke(input_data)


    return results


######### 4. Save the extracted data to CSV #################
def save_to_csv(data, csv_file_path):

    # Parse the string response to JSON
    try:
        data = json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return

    # Extract the headers from the first dictionary (keys of the dictionary)
    headers = data[0].keys()

    # Open the CSV file for writing
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        # Create a CSV DictWriter object
        writer = csv.DictWriter(csv_file, fieldnames=headers)

        # Write the header row
        writer.writeheader()

        # Write the data rows
        for row in data:
            writer.writerow(row)

    print(f"Data has been successfully saved to {csv_file_path}")

######### 5. Upload CSV to S3 #################
def upload_csv_to_s3(bucket_name, s3_key, local_file_path):
    s3_client.upload_file(local_file_path, bucket_name, s3_key)

######### 6. Run the App with input fields #################
def main():
    # Define the S3 bucket and file key
    bucket_name = 'my-pdf-processing-ai-bucket'
    s3_key = 'Group_Rates_small.pdf'  # Assuming the file is at the root of the bucket
    local_pdf_path = '/tmp/Group_Rates_small.pdf'
    local_csv_path = '/tmp/extracted_data.csv'
    s3_csv_key = 'processed-data/extracted_data.csv'  # Uploading to a specific folder

    # Download the PDF from S3
    download_pdf_from_s3(bucket_name, s3_key, local_pdf_path)

    # Define the output variables we want to get
    default_data_points = """{
    "room_config": "What is the type of room that is available, for example 'Superior 2 Bedroom Cabin Sleeps 4'.",
    "High_season_rate": "How much does this room cost in high season?",
    "destination": "What is the destination that offers services or accommodation?"
    }"""

    # Extract content from PDF
    content = extract_text_tables_pdf(local_pdf_path)

    # Extract structured data
    data = extract_structured_data(content, default_data_points)

    # Save the extracted data to a CSV file
    save_to_csv(data, local_csv_path)

    # Upload the CSV file back to S3
    upload_csv_to_s3(bucket_name, s3_csv_key, local_csv_path)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()