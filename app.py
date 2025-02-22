import streamlit as st
import pymupdf
from gemini_client import create_client, summarize_cim 
from get_access_token import get_access_token
from secure_gpt_api import chat_with_api
from io import StringIO
from google.cloud import storage
import vertexai 

# Upload file to GCS
def upload_blob(bucket_name, destination_blob_name, file):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)

    st.write("File:  ", destination_blob_name, "  uploaded to GCS.")

project_id = "ai-ml-team-sandbox"
location = "us-central1"
bucket_name = "kjr-veolia-test"
folder = "cim_documents/pdf"

# Define locataion of the CIM Outline 
outline_name = "CIMOutline.pdf"

# API URL
token_url = "https://api.veolia.com/security/v2/oauth/token"
api_url = 'https://api.veolia.com/llm/veoliasecuregpt/v1/answer'

# Get access token and init Vertex
access_token = get_access_token(token_url, api_url)
vertexai.init(project=project_id, location="us-central1")

# Init Gemini client
gemini_client = create_client(project_id, location)

st.title("Text Extraction and Memo Generation")
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    st.write("File uploaded successfully!")
    # Upload the pdf file to GCS 
    upload_blob(bucket_name, f"{folder}/{uploaded_file.name}", uploaded_file)

    # Get the outline from Gemini
    summary_from_gemini = summarize_cim(gemini_client, f"gs://{bucket_name}/{folder}/{uploaded_file.name}",
                                        f"gs://{bucket_name}/{outline_name}")
    st.write(summary_from_gemini)