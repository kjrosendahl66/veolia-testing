import streamlit as st
from google.cloud import storage
import vertexai
import os
from datetime import datetime
from dotenv import load_dotenv
import tempfile
import pymupdf
from gemini_client import create_client, summarize_cim, format_summary_as_markdown
from get_access_token import get_access_token
from document_funcs import render_files, save_summary_as_docx
from chatbot import chatbot_tab


# Upload file to GCS
def upload_blob(bucket_name, destination_blob_name, file):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)

    return f"gs://{bucket_name}/{destination_blob_name}"


# Render markdown for streamlit
def render_markdown(text):
    text = text.replace("\\", "\\\\").replace("$", "\$").replace("<br>", " ")
    return text


# Set configuration and title
st.set_page_config(layout="wide")

# Load environment variables
load_dotenv()
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")
bucket_name = os.getenv("BUCKET_NAME")
service_account = os.getenv("SERVICE_ACCOUNT")

# Initialize Vertex AI
vertexai.init(project=project_id, location=location)

# Get access token for SecureGPT
token_url = "https://api.veolia.com/security/v2/oauth/token"
api_url = "https://api.veolia.com/llm/veoliasecuregpt/v1/answer"
access_token = get_access_token(token_url, api_url)

# Initialize session state
if "files" not in st.session_state:
    st.session_state.files = {}
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if "docs" not in st.session_state:
    st.session_state.docs = {}
# if "model_option" not in st.session_state:
#     st.session_state.model_option = "gemini-2.0-flash"
st.session_state.markdown_gemini_client = create_client(
    model_name="gemini-1.5-flash", chatbot=False
)

tab1, tab2 = st.tabs(["Home", "Chatbot"])

# Display the home tab
with tab1:
    st.title("V-Accelerate")
    # st.write(" \n  ")
    st.subheader("Create initial summaries and ask questions of your Confidential Information Memorandum (CIM)!", divider="gray")


    # Model selection and file input
    model_option = st.selectbox(
        label="Choose a model to generate a summary:",
        options=("gemini-2.0-flash","gemini-1.5-pro", "Secure GPT"),
        index=None, 
        placeholder="Select a model...",
    )
    uploaded_files = st.file_uploader(
        "Upload your CIM and outline template:", type=["pdf"], accept_multiple_files=True
    )

    if model_option:
        st.session_state.model_option = model_option

    if len(uploaded_files) > 1:
        # Process input files
        if not st.session_state.files:
            with st.spinner("Processing files..."):
                # Create a timestamp for the files
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

                for file in uploaded_files:
                    # Upload the files to GCS for the LLM
                    gcs_location = upload_blob(
                        bucket_name, f"files/{timestamp}/{file.name}", file
                    )
                    # Save the files to a temp directory
                    path = os.path.join(st.session_state.temp_dir, file.name)
                    with open(path, "wb") as f:
                        f.write(file.getvalue())

                    # Save locations of the files to the session state
                    st.session_state.files.update(
                        {
                            file.name: {
                                "local_file_location": path,
                                "gcs_file_location": gcs_location,
                            }
                        }
                    )

                    # Open and save the rendered PDF files as pymupdf docs to the session state
                    st.session_state.docs[file.name] = pymupdf.open(path)

            st.toast("Files processed succesfully!", icon="🎉")

        # Generate summary
        if len(st.session_state.files) > 1 and "summary" not in st.session_state and model_option:
            with st.spinner("Generating summary..."):
                # Generate summary using Gemini
                if model_option.startswith("gemini"):
                    # Create a client
                    gemini_client = create_client(
                        model_name=st.session_state.model_option
                    )

                    # Generate main summary
                    summary_from_gemini = summarize_cim(
                        gemini_client, st.session_state.files
                    )
                    # Generate a summary for markdown display in streamlit
                    display_summary = format_summary_as_markdown(
                        st.session_state.markdown_gemini_client, summary_from_gemini
                    )

                    # Save both summaries to the session state
                    st.session_state.summary = summary_from_gemini
                    st.session_state.display_summary = display_summary

                elif model_option == "Secure GPT":
                    st.session_state.summary = "Secure GPT not implemented yet. "

        #  Display markdown summary
        if "display_summary" in st.session_state:
            # Render the markdown summary and display in streamlit
            st.markdown(
                render_markdown(st.session_state.display_summary),
                unsafe_allow_html=True,
            )

            # Save the summary as a docx file
            output_path, output_filename = save_summary_as_docx(
                st.session_state.summary
            )

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
        container = st.container(border=True)
        with container:
            render_files()

with tab2:
    chatbot_tab()
