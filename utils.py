from google.cloud import storage

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

