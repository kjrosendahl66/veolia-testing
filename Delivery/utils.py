from google.cloud import storage
from datetime import datetime
import os 
import streamlit as st
import pymupdf 

def upload_blob(bucket_name, destination_blob_name, file):
    """ 
    This function uploads a file to a specified bucket in Google Cloud Storage.
    Args:
        bucket_name (str): The name of the bucket to upload to. 
        destination_blob_name (str): The name of the file in the bucket.
        file: The file to upload.
    Returns:
        str: The full GCS URL of the uploaded file.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_file(file)

    return f"gs://{bucket_name}/{destination_blob_name}"

# Render markdown for streamlit
def render_markdown(text):
    text = text.replace("\\", "\\\\").replace("$", "\$").replace("<br>", " ")
    return text


def upload_gcs_and_save(bucket_name, file, file_type):
    """ 
    This function uploads a file to GCS and saves the file information to the session state.
    Args: 
        bucket_name (str): The name of the bucket to upload to.
        file: The file to upload.
        file_type (str): The type of file being uploaded. Either "document", "template", or "memo". 
    Returns:
        str: The local path to the uploaded file.
    """

    # Create a timestamp for the files
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Upload the files to GCS 
    gcs_location = upload_blob(
        bucket_name, f"files/{timestamp}/{file.name}", file
    )

    # Save file to local path for rendering
    path = os.path.join(st.session_state.temp_dir, file.name)
    with open(path, "wb") as f:
        f.write(file.getvalue())

    # Save locations of the files to the session state
    st.session_state.files.update(
        {
            file.name: {
                "file_type": file_type, # "document", "template", or "memo"
                "local_file_location": path, # Local path to the file
                "gcs_file_location": gcs_location, # GCS path to the file
                "mime_type": file.type, # Mime type of the file
                "doc": pymupdf.open(path)  # Opened document for rendering
            }
        }
    )

    return path
