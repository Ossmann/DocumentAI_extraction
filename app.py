
import fitz
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import multiprocessing

# load the OpenAI API Key from environment variables
load_dotenv()


######### 1. Get PDF text and tables as markup #################
def extract_text_tables_pdf(file):
    # Create a document object
    doc = fitz.open('Group_Rates_small.pdf')

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
    

######### 2. Extract structured info from text via LLM #################

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

#### 3. Run the App with input fields

def main():
    #define the putput variables we want to get
    default_data_points = """{
    "room_config": "What is the type of room that is available, for example 'Superior 2 Bedroom Cabin Sleeps 4'. tters.",
    "High_season_rate": "How much does this room cost in high season?"
    "destination: "What is the destination that offers services or accomodation?"
    }"""

    content = extract_text_tables_pdf("Group_Rates_small.pdf")
    data = extract_structured_data(content, default_data_points)

    print(data)

if __name__ == '__main__' :
    multiprocessing.freeze_support()
    main()
