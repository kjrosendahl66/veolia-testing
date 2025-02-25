import streamlit as st
from google.cloud import storage
import vertexai 
import os 
from datetime import datetime 
from dotenv import load_dotenv
import tempfile
import json
import re
import pymupdf
import pypandoc
from gemini_client import create_client, summarize_cim, format_summary_as_markdown
from get_access_token import get_access_token
from secure_gpt_api import chat_with_api
from reference_display import render_files
import pypandoc

# Upload file to GCS
def upload_blob(bucket_name, destination_blob_name, file):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)

    return f"gs://{bucket_name}/{destination_blob_name}"

def render_markdown(text):
    text = text.replace("$", "\$").replace("<br>", "")
    return text

st.set_page_config(layout="wide")
st.title("V-Accelerate: Memo Generation Tool") 
st.write(" \n  ")
st.write(" \n  ")

load_dotenv()

project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")
bucket_name = os.getenv("BUCKET_NAME")

# API URL
token_url = "https://api.veolia.com/security/v2/oauth/token"
api_url = 'https://api.veolia.com/llm/veoliasecuregpt/v1/answer'

# Get access token and init Vertex
access_token = get_access_token(token_url, api_url)

if "files" not in st.session_state: 
    st.session_state.files = {}
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if "docs" not in st.session_state:
    st.session_state.docs = {}


model_option = st.selectbox(label="Select the model to use", options=("gemini-1.5-pro", "gemini-2.0-flash", "Secure GPT"))
uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

if len(uploaded_files) > 1: 
    if not st.session_state.files:

        with st.spinner("Processing files..."):

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            for file in uploaded_files:
                # Upload the files to GCS for the LLM
                uploaded_location = upload_blob(bucket_name, f"files/{timestamp}/{file.name}", file)
                # Save the files to the temp directory for rendering
                path = os.path.join(st.session_state.temp_dir, file.name)
                with open(path, "wb") as f:
                    f.write(file.getvalue())

                # Save the file locations
                st.session_state.files.update(
                    {file.name: 
                        {"local_file_location": path, 
                        "gcs_file_location": uploaded_location
                        }
                    }
                )

                st.session_state.docs[file.name] = pymupdf.open(path)

        st.toast('Files processed succesfully!', icon='🎉')

    if len(st.session_state.files) > 1 and "summary" not in st.session_state:
        with st.spinner("Generating summary..."):

            if model_option.startswith("gemini"): 
                
                gemini_client = create_client(project_id, location, model_name=model_option)

                summary_from_gemini = summarize_cim(gemini_client, st.session_state.files)
                display_summary = format_summary_as_markdown(gemini_client, summary_from_gemini)

                st.session_state.summary = summary_from_gemini 
                st.session_state.display_summary = display_summary

            elif model_option == "Secure GPT": 
                st.session_state.summary= "Secure GPT not implemented yet. "

    if st.session_state.display_summary: 

        st.markdown(render_markdown(st.session_state.display_summary), unsafe_allow_html=True)
        st.text(st.session_state.display_summary)

        markdown_filename = "summary.md"
        output_filename = "summary.docx"
        markdown_path = os.path.join(st.session_state.temp_dir, markdown_filename)
        output_path = os.path.join(st.session_state.temp_dir, output_filename)

        with open(markdown_path, "w") as f:
            f.write(st.session_state.summary)

        pypandoc.convert_file(markdown_path, 'docx', outputfile=output_path)
        
        download = st.download_button(
            label="Download summary as a docx!",
            data=open(output_path, "rb").read(),
            file_name=output_filename,
        )
    
else: 
    st.write("Please upload at least two files to get started.")

with st.sidebar: 
    container = st.container(border = True)
    with container:
        render_files()

