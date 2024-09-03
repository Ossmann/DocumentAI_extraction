# Project Name
DocumentAI data extraction

## Overview
We extact text and table data from pdf and use AI to get specific infos.

## Installation
Use fitz (former pyMuPdf) for extraction.\
Use langchain to pass text with instructions prompt to AI.
Use OpenAI API to return curated values. 

## Usage

## Acknowledgments
### 


## Resources
Check out Pythonology for fitz (pyMuPDF)
- [Pythonology] (https://www.youtube.com/watch?v=G0PApj7YPBo)

Check Out AI Jason for langchain application, but check out langchain docu for latest functions
- [AI Jason's YouTube Tutorial](https://www.youtube.com/watch?v=v_cfORExneQ)


## Update

**Update:**
Use the following import instead of the older one:

```python
from langchain_openai import ChatOpenAI
```
Instead of:
```python
from langchain.chat_models import ChatOpenAI
```

```python
input_data = {
        "content": content,
        "data_points": data_points
    }

    chain = prompt | llm | StrOutputParser()

    results = chain.invoke(input_data)
```

Instead of:
```python
chain = LLMChain(llm=llm, prompt=prompt)
```