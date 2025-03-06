# V-Accelerate
---

## Overview
The purpose of V-Accelerate is to provide a unified interface for generating Confidential Information Memorandums (CIMs) and drafting memos using Large Language Models (LLMs). Key features include: 
- Generation of CIM summaries using uploaded CIM templates and supporting documents. 
- Generation of formatted memo drafts. 
- Chatbot for making edits to CIM summaries. 
- Chatbot for answering questions about uploaded documents. 

## Structure 

```
├── Delivery    # Module for app 
│   ├── app.py      # Main entrypoint for Streamlit App
│   ├── chatbots.py     
|   ├── Dockerfile
│   ├── document_manager.py
│   ├── get_access_token.py
|   ├── images      
|   │   ├── 66degreesBlack.png
|   │   ├── poweredLogo_processed.png
|   │   └── veolia.png
│   ├── llm_manager.py
│   ├── memo_elements       # Formatting headers
│   │   ├── headings.txt
│   │   └── subheadings.txt
│   ├── memo_formatter.py
│   ├── secure_gpt_api.py
│   └── utils.py        
├── Notebooks
│   └── interact_gpt_api.ipynb
├── Python.gitignore
└── requirements.txt
```
The main entrypoint `Delivery/app.py` relies on several files to run: 
- `chatbots.py`: Displays Editor and Q&A Chats. 
- `document_manager.py`: Renders files and document file explorer. 
- `llm_manager.py`: Manages LLM system instructions, requests, and calls. 
- `memo_formatter.py`: Formats memo using the Google Docs API and exports to a DOCX file. 
- `utils.py`: Processes and uploads files for the LLM.  

## Setup 
1. Clone repo and navigate to folder: 
``` 
cd Delivery/app
``` 

2. (Optional) Create a virtual environment: 
```
python -m venv app
source app/bin/activate
pip install -r requirements.txt
```

3. Set environment variables. See `env.example`. 
4. Run app locally: 
```
streamlit run app.py
```
