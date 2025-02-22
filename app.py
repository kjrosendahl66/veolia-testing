import streamlit as st
import pymupdf
from gemini_client import create_client, summarize_cim 
from get_access_token import get_access_token
from secure_gpt_api import chat_with_api
from google.cloud import storage
import vertexai 
import os 
from datetime import datetime 
from dotenv import load_dotenv


# Upload file to GCS
def upload_blob(bucket_name, destination_blob_name, file):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)

    st.write("File:  ", destination_blob_name, "  uploaded to GCS.")
    return f"gs://{bucket_name}/{destination_blob_name}"

load_dotenv()

project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")
bucket_name = os.getenv("BUCKET_NAME")

# # Define locataion of the CIM Outline 
# outline_name = "CIMOutline.pdf"

# API URL
token_url = "https://api.veolia.com/security/v2/oauth/token"
api_url = 'https://api.veolia.com/llm/veoliasecuregpt/v1/answer'

# Get access token and init Vertex
access_token = get_access_token(token_url, api_url)
vertexai.init(project=project_id, location="us-central1")

# Init Gemini client
gemini_client = create_client(project_id, location)

st.title("Text Extraction and Memo Generation")
uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

if len(uploaded_files) > 1: 
    st.write("Files uploaded successfully!")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_locations = []

    # Upload the files to GCS 
    for file in uploaded_files:
        file_location = upload_blob(bucket_name, f"files/{timestamp}/{file.name}", file)
        file_locations.append(file_location)

    # Get the outline from Gemini
    summary_from_gemini = summarize_cim(gemini_client, file_locations) 

    st.write(summary_from_gemini)

else: 
    st.write("Please upload at least two files to proceed.")