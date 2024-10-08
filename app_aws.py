import fitz  # former pyMuPDF
import boto3
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import multiprocessing
import os
import csv
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the OpenAI API Key from environment variables
load_dotenv()

# Initialize S3 client
s3_client = boto3.client('s3')

######### 1. Download PDF from S3 #################
def download_pdf_from_s3(bucket_name, s3_key, local_file_path):
    try:
        logging.info(f"Downloading {s3_key} from bucket {bucket_name} to {local_file_path}")
        s3_client.download_file(bucket_name, s3_key, local_file_path)
        logging.info("Download complete")
    except Exception as e:
        logging.error(f"Failed to download file from S3: {e}")
        raise

######### 2. Get PDF text and tables as markup #################
def extract_text_tables_pdf(file_path):
    logging.info(f"Extracting text and tables from PDF: {file_path}")
    doc = fitz.open(file_path)
    pdf_markup = ""
    page_count = doc.page_count
    logging.info(f"Number of pages in PDF: {page_count}")

    for i in range(page_count):
        page = doc.load_page(i)
        tabs = list(page.find_tables())
        logging.info(f"Found {len(tabs)} tables on page {i + 1}")

        table_areas = []
        for tab in tabs:
            for cell in tab.cells:
                table_areas.append(cell[:4])

        for i, tab in enumerate(tabs):
            table_data = tab.extract()
            for row_index, row_content in enumerate(table_data):
                logging.info(f"Table {i + 1} - Row {row_index}: {row_content}")

        all_text = page.get_text("markdown")
        non_table_text = all_text
        for area in table_areas:
            clip_rect = fitz.Rect(area)
            non_table_text = all_text.replace(page.get_text("markdown", clip=clip_rect), "")

        pdf_markup += f"Text on page {i + 1}:\n{non_table_text}\n"

    logging.info("Text and table extraction complete")
    return pdf_markup

######### 3. Extract structured info from text via LLM #################
def extract_structured_data(content: str, data_points):
    logging.info("Extracting structured data using LLM")
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        template = """
        You are an expert admin people who will extract core information from documents

        {content}

        Above is the content; please try to extract all data points from the content above 
        and export in a JSON array format:
        {data_points}

        Now please extract details from the content  and export in a JSON array format, 
        return ONLY the JSON array:
        """

        prompt = PromptTemplate(input_variables=["content", "data_points"], template=template)
        input_data = {"content": content, "data_points": data_points}
        chain = prompt | llm | StrOutputParser()
        results = chain.invoke(input_data)
        logging.info("Structured data extraction complete")
        return results
    except Exception as e:
        logging.error(f"Failed to extract structured data: {e}")
        raise

######### 4. Save the extracted data to CSV #################
def save_to_csv(data, csv_file_path):
    logging.info(f"Saving extracted data to CSV: {csv_file_path}")
    try:
        data = json.loads(data)
        headers = data[0].keys()

        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

        logging.info(f"Data successfully saved to {csv_file_path}")
    except Exception as e:
        logging.error(f"Failed to save data to CSV: {e}")
        raise

######### 5. Upload CSV to S3 #################
def upload_csv_to_s3(bucket_name, s3_key, local_file_path):
    try:
        logging.info(f"Uploading {local_file_path} to bucket {bucket_name} with key {s3_key}")
        s3_client.upload_file(local_file_path, bucket_name, s3_key)
        logging.info("Upload complete")
    except Exception as e:
        logging.error(f"Failed to upload CSV to S3: {e}")
        raise

######### 6. Run the App with input fields #################
def main(bucket_name, s3_key):
    logging.info("Starting the PDF processing script")
    local_pdf_path = f'/tmp/{os.path.basename(s3_key)}'
    local_csv_path = f'/tmp/{os.path.splitext(os.path.basename(s3_key))[0]}_extracted_data.csv'
    s3_csv_key = f'processed-data/{os.path.splitext(os.path.basename(s3_key))[0]}_extracted_data.csv'

    try:
        download_pdf_from_s3(bucket_name, s3_key, local_pdf_path)
        default_data_points = """{
            "room_config": "What is the type of room that is available, for example 'Superior 2 Bedroom Cabin Sleeps 4'.",
            "High_season_rate": "How much does this room cost in high season?",
            "destination": "What is the destination that offers services or accommodation?"
        }"""
        content = extract_text_tables_pdf(local_pdf_path)
        data = extract_structured_data(content, default_data_points)
        save_to_csv(data, local_csv_path)
        upload_csv_to_s3(bucket_name, s3_csv_key, local_csv_path)
    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    if len(sys.argv) != 3:
        logging.error("Usage: python app_aws.py <bucket_name> <s3_key>")
        sys.exit(1)
    bucket_name = sys.argv[1]
    s3_key = sys.argv[2]
    main(bucket_name, s3_key)