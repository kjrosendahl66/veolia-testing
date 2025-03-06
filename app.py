import streamlit as st
import vertexai
import os
from datetime import datetime
from dotenv import load_dotenv
import tempfile
import pymupdf
from get_access_token import get_access_token
from llm_manager import create_client, summarize_cim, format_summary_as_markdown, create_memo
from document_manager import render_files, display_download_buttons
from chatbots import editor_chabot, qa_chatbot
from utils import render_markdown, upload_gcs_and_save
from document_manager import render_files, display_download_buttons, convert_docx_to_pdf
from memo_formatter import format_and_export_memo, fetch_headers

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


# ----------------- # 
# """
# # Files in session state are used to send to the LLM and render in the UI. 
# # Example: 
# # st.session_state.files = {
# #     "file1.pdf": {
# #         "file_type": "document/template",
# #         "local_file_location": "path/to/file1.pdf",
# #         "gcs_file_location": "gs://bucket_name/path/to/file1.pdf",
# #         "mime_type": "application/pdf",
# #         "doc": pymupdf.open("path/to/file1.pdf")
# """ 
if "files" not in st.session_state:
    st.session_state.files = {}

# Initialize session state variables 
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
st.session_state.markdown_gemini_client = create_client(
    model_name="gemini-1.5-flash"
)
if "memo_filename" not in st.session_state:
    st.session_state.memo_filename = None
if "memo_text" not in st.session_state:
    st.session_state.memo_text = None

st.image("images/veolia.png", width=200) # Adjust width as needed

tab1, tab2, tab3 = st.tabs(["Home", "Editor Chatbot", "Q&A Chatbot"])

# Display the home tab
with tab1:
    st.title("V-Accelerate")
    st.markdown("_Create initial summaries and ask questions of your Confidential Information Memorandum (CIM)!_")

    # Model selection
    model_option = st.selectbox(
        label="Choose a model to generate a summary:",
        options=("gemini-2.0-flash","gemini-1.5-pro", "Secure GPT"),
        index=None, 
        placeholder="Select a model...",
    )

    # File upload for CIM template outline 
    uploaded_template = st.file_uploader(
        "Upload your CIM template:", type=["pdf", "txt"], accept_multiple_files=True
    )

    # File upload for information documents
    uploaded_files = st.file_uploader(
        "Upload your files:", type=["pdf", "txt"], accept_multiple_files=True
    )
        
    # Save model option for LLM 
    if model_option:
        st.session_state.model_option = model_option

    if len(uploaded_template) > 0 and len(uploaded_files) > 0 and len(st.session_state.files) == 0:

        # Load and upload files to GCS 
        with st.spinner("Processing files..."):

            # Create a timestamp for the files
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            # Upload the information documents to GCS and save to session 
            for file in uploaded_files:
                path = upload_gcs_and_save(bucket_name, file, "document")

            # Upload the template to GCS and save to session
            for file in uploaded_template:
                path = upload_gcs_and_save(bucket_name, file, "template")

        st.toast("Files processed succesfully!", icon="🎉")

        # Generate CIM summary and memo 
        if len(st.session_state.files) > 1 and "summary" not in st.session_state and model_option:

            with st.spinner("Generating summary..."):

                # Generate summary using Gemini
                if model_option.startswith("gemini"):

                    # Create a client
                    gemini_client = create_client(
                        model_name=st.session_state.model_option
                    )

                    # Generate a summary using the uploaded files
                    summary_from_gemini = summarize_cim(
                        model=gemini_client,
                        files=st.session_state.files
                    )

                    # Format the summary as markdown
                    display_summary = format_summary_as_markdown(
                        model=st.session_state.markdown_gemini_client, 
                        summary=summary_from_gemini
                    )

                    # Save both summaries to the session state
                    st.session_state.summary = summary_from_gemini
                    st.session_state.display_summary = display_summary

                    # Generate a memo draft 
                    if st.session_state.memo_text is None:

                        # Read the headings and subheadings as lists for formatting the memo 
                        headings = fetch_headers('memo_elements/headings.txt')
                        subheadings = fetch_headers('memo_elements/subheadings.txt')

                        # Generate the memo using Gemini 
                        memo_text = create_memo(
                                    model=gemini_client, 
                                    files=st.session_state.files,
                                    headings=headings, subheadings=subheadings)
                        st.session_state.memo_text = memo_text
                        
                    # Format the memo according to memo outline 
                    if st.session_state.memo_filename is None:

                        # Format memo and export to a docx file 
                        memo_filename = "memo_draft.docx"
                        st.session_state.memo_filename = format_and_export_memo(filename=memo_filename)

                        # Convert the memo to a PDF file
                        try: 
                            pdf_filename = "memo.pdf"
                            memo_output_path, memo_filename = convert_docx_to_pdf(
                                docx_path=st.session_state.memo_filename, 
                                output_pdf_filename=pdf_filename)

                            # Save the rendered memo to the session state
                            st.session_state.files["Memo"] = {"doc": pymupdf.open(memo_output_path)}
                        except Exception as e:
                            st.error("Error converting memo to PDF. Please try again.")
        
                elif model_option == "Secure GPT":
                    st.session_state.summary = "Secure GPT not implemented yet. "

    #  Display markdown summary
    if "display_summary" in st.session_state:

        # Render the markdown summary and display in streamlit
        st.markdown(
            render_markdown(st.session_state.display_summary),
            unsafe_allow_html=True,
        )

        st.divider()
    
        # Display download buttons for the summary
        display_download_buttons(summary_name="summary")

    else:
        st.write("Please upload at least two files and choose a model.")

    # Display download memo draft button
    if st.session_state.memo_filename:
        st.divider() 
        _ = st.download_button(
            label = "Download Memo Draft",
            data = open(st.session_state.memo_filename, "rb").read(),
            file_name = st.session_state.memo_filename,
            key="memo_download")


    # Display the uploaded files in the sidebar
    with st.sidebar:
        container = st.container(border=True)
        with container:
            render_files()


# Display the editor chatbot tab
with tab2:
    if "summary" in st.session_state and model_option:
        editor_chabot()
    else: 
        st.write("Please generate a summary in the Home tab first.")

# Display the Q&A chatbot tab
with tab3:
    if len(st.session_state.files) > 0 and model_option:
        qa_chatbot()
    else: 
        st.write("Please upload files and choose a model in the Home tab first.")


st.logo("images/poweredLogo_processed.png")