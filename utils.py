from google.cloud import storage
from datetime import datetime
import os 
import streamlit as st
import pymupdf 

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


def upload_gcs_and_save(bucket_name, file, file_type):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

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
                "file_type": file_type,
                "local_file_location": path,
                "gcs_file_location": gcs_location,
                "mime_type": file.type,
                "doc": pymupdf.open(path)
            }
        }
    )


                # # Open and save the rendered PDF files as pymupdf docs to the session state
                # st.session_state.docs[file.name] = pymupdf.open(path)

    return path
