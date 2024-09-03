# Project Name
DocumentAI data extraction

## Overview

## Installation

## Usage
Use to extract predefined infos from pdfs with the hep of pytesseract OCR and OpenAI.

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

## Acknowledgments
### 
Thank you to AI Jason for instructions

## Resources
Link to any resources or tutorials you found helpful.

- [AI Jason's YouTube Tutorial](https://www.youtube.com/watch?v=v_cfORExneQ)