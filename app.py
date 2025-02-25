import streamlit as st
from google.cloud import storage
import os 
from datetime import datetime 
from dotenv import load_dotenv
import tempfile
import pymupdf
import pypandoc
from gemini_client import create_client, summarize_cim, format_summary_as_markdown
from get_access_token import get_access_token
from reference_display import render_files

# Upload file to GCS
def upload_blob(bucket_name, destination_blob_name, file):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)

    return f"gs://{bucket_name}/{destination_blob_name}"

# Render markdown for streamlit 
def render_markdown(text):
    text = text.replace("$", "\$").replace("<br>", "")
    return text

# Set configuration and title 
st.set_page_config(layout="wide")
st.title("V-Accelerate: Memo Generation Tool") 
st.write(" \n  ")
st.write(" \n  ")

# Load environment variables
load_dotenv()
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")
bucket_name = os.getenv("BUCKET_NAME")

# Get access token for SecureGPT 
token_url = "https://api.veolia.com/security/v2/oauth/token"
api_url = 'https://api.veolia.com/llm/veoliasecuregpt/v1/answer'
access_token = get_access_token(token_url, api_url)

# Initialize session state
if "files" not in st.session_state: 
    st.session_state.files = {}
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if "docs" not in st.session_state:
    st.session_state.docs = {}

# Model selection and file input
model_option = st.selectbox(label="Select the model to use", options=("gemini-1.5-pro", "gemini-2.0-flash", "Secure GPT"))
uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

if len(uploaded_files) > 1: 

    # Process input files
    if not st.session_state.files:

        with st.spinner("Processing files..."):

            # Create a timestamp for the files
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            for file in uploaded_files:
                # Upload the files to GCS for the LLM
                gcs_location = upload_blob(bucket_name, f"files/{timestamp}/{file.name}", file)
                # Save the files to a temp directory
                path = os.path.join(st.session_state.temp_dir, file.name)
                with open(path, "wb") as f:
                    f.write(file.getvalue())

                # Save locations of the files to the session state
                st.session_state.files.update(
                    {file.name: 
                        {"local_file_location": path, 
                        "gcs_file_location": gcs_location
                        }
                    }
                )

                # Open and save the rendered PDF files as pymupdf docs to the session state
                st.session_state.docs[file.name] = pymupdf.open(path)

        st.toast('Files processed succesfully!', icon='🎉')

    # Generate summary 
    if len(st.session_state.files) > 1 and "summary" not in st.session_state:

        with st.spinner("Generating summary..."):

            # Generate summary using Gemini 
            if model_option.startswith("gemini"): 
                
                # Create a client
                gemini_client = create_client(project_id, location, model_name=model_option)

                # Generate main summary
                summary_from_gemini = summarize_cim(gemini_client, st.session_state.files)
                # Generate a summary for markdown display in streamlit
                display_summary = format_summary_as_markdown(gemini_client, summary_from_gemini)

                # Save both summaries to the session state
                st.session_state.summary = summary_from_gemini 
                st.session_state.display_summary = display_summary

            elif model_option == "Secure GPT": 
                st.session_state.summary= "Secure GPT not implemented yet. "

    #  Display markdown summary 
    if st.session_state.display_summary: 

        # Render the markdown summary and display in streamlit 
        st.markdown(render_markdown(st.session_state.display_summary), unsafe_allow_html=True)
        
        # Declare variables for downloading the summary as a docx
        summary_filename = "summary.md"
        output_filename = "summary.docx"
        summary_path = os.path.join(st.session_state.temp_dir, summary_filename)
        output_path = os.path.join(st.session_state.temp_dir, output_filename)

        # Save the summary to a local path
        with open(summary_path, "w") as f:
            f.write(st.session_state.summary)

        # Convert the summary to a docx file
        pypandoc.convert_file(summary_path, 'docx', outputfile=output_path)
        
        # Display a download button for the docx file
        download = st.download_button(
            label="Download summary as a docx!",
            data=open(output_path, "rb").read(),
            file_name=output_filename,
        )
    
else: 
    st.write("Please upload at least two files to get started.")

# Display the uploaded files in the sidebar
with st.sidebar: 
    container = st.container(border = True)
    with container:
        render_files()

