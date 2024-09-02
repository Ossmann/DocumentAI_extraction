
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from pytesseract import image_to_string
from PIL import Image
from io import BytesIO
import pypdfium2 as pdfium
import streamlit as st
import multiprocessing
from tempfile import NamedTemporaryFile
import pandas as pd
import json
import requests
import time


# load the OpenAI API Key from environment variables
load_dotenv()


#### 1. Convert PDF file into images via pydpdfium2

def convert_pdf_to_images(file_path, scale=300/72):

    pdf_file = pdfium.PdfDocument(file_path)

    page_indices = [i for i in range(len(pdf_file))]

    renderer = pdf_file.render(
        pdfium.PdfBitmap.to_pil,
        page_indices=page_indices,
        scale=scale,
    )

    final_images = []

    for i, image in zip(page_indices, renderer):

        image_byte_array = BytesIO()
        image.save(image_byte_array, format='jpeg', optimize=True)
        image_byte_array = image_byte_array.getvalue()
        final_images.append(dict({i: image_byte_array}))

    return final_images

#### 2. Extract text from images via pytesseract

def extract_text_from_img(list_dict_final_images):

    image_list = [list(data.values())[0] for data in list_dict_final_images]
    image_content = []

    for index, image_bytes in enumerate(image_list):

        image = Image.open(BytesIO(image_bytes))
        raw_text = str(image_to_string(image))
        image_content.append(raw_text)

    return "\n".join(image_content)

# call function from step 1. and to pass the images to 
def extract_content_from_url(url: str):

    start_time = time.time()  # Record the start time


    images_list = convert_pdf_to_images(url)
    text_with_pytesseract = extract_text_from_img(images_list)

    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate elapsed time

    print(f"Function execution time: {elapsed_time:.2f} seconds")  # Display the elapsed time

    return text_with_pytesseract

#### 3. Extract structured info from text via LLM

def extract_structured_data(content: str, data_points):
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613") #Set the LLM model and give it instructions message
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

    chain = LLMChain(llm=llm, prompt=prompt)

    results = chain.run(content=content, data_points=data_points)

    return results

#### 4. Send data to make.com via webhook

def main():
    default_data_points = """{
    "room_type": "What is the type of room that is available",
    "High_season_rate": "How much does this room cost in high season?"
    "destination: "What is the destination that offers services or accomodation?"
    }"""

    content = extract_content_from_url("Group_Rates.pdf")
    data = extract_structured_data(content, default_data_points)

    print(data)

if __name__ == '__main__' :
    multiprocessing.freeze_support()
    main()
