from googleapiclient.discovery import build
import google.auth
from google.auth import impersonated_credentials
import streamlit as st
from typing import List
import os

def fetch_headers(file: str): 
    """ 
    This function reads a file and returns a list of headers.
    Args:
        file (str): The file to read.
    Returns:
        list: A list of headers.
    """
    headers = []
    with open(file, "r") as f:
        for line in f:
            headers.append(line.strip())
    return headers

def read_text(service: object, document_id: str): 
    """ 
    This function reads the text from a Google Doc using the Docs API. 
    Args:
        service (googleapiclient.discovery.Resource): The Docs API service.
        document_id (str): The ID of the document to read.
    Returns:
        text (str): The text from the document.
        start_index (int): The start index of the document.
        end_index (int): The end index of the document.
    """
    # Retrive document 
    document = service.documents().get(documentId=document_id).execute()

    # Fetch text
    text = ""
    start_index = 0
    if 'body' in document:
        for element in document['body']['content']:
            if 'paragraph' in element:
                for paragraph_element in element['paragraph']['elements']:
                    if 'textRun' in paragraph_element:
                        text += paragraph_element['textRun']['content']
                    #Check for section breaks, and update start index if found.
            if 'sectionBreak' in element:
                start_index = element['endIndex']

    # Calculate the end index of the document 
    end_index = len(text) + start_index

    return text, start_index, end_index


def create_document(service: object, title: str):
    """
    This function creates a new Google Doc using the Docs API.
    Args:
        service (googleapiclient.discovery.Resource): The Docs API service.
        title (str): The title of the document.
    Returns:
        doc_id (str): The ID of the newly created document.
    """

    body = {
        'title': title} 

    # Create the document
    doc = service.documents().create(body=body).execute()

    return doc['documentId']

def add_text(service: object, document_id: str, text: str): 
    """
    This function populates the body of a Google Doc with text.

    Args:
        service (googleapiclient.discovery.Resource): The Docs API service.
        document_id (str): The ID of the document to update.
        text (str): The text to add to the document.
        
    """
    requests = [
                {
                    "insertText": {
                        "location": {"index": 1},  # Insert at the beginning of the document 
                        "text": text,
                    }
                }
            ]

    body = {"requests": requests}

    # Submit the request update 
    service.documents().batchUpdate(documentId=document_id, body=body).execute()

def format_document(service: object, document_id: str, heading_titles: List[str], subheading_titles: List[str]):
    """
    This document performs a series of batch updates to the Docs API to format the Google Doc memo. 
    Args:
        service (googleapiclient.discovery.Resource): The Docs API service.
        document_id (str): The ID of the document to format.
        heading_titles (list): A list of heading titles.
        subheading_titles (list): A list of subheading titles.
    Returns:
        None
    """

    # Read the text body of the document 
    text, start_index, end_index = read_text(service, document_id)

    # Set the style of the headings to Heading 1 
    requests = []
    for title in heading_titles:
        title_index = text.find(title) # Find the index of the title in the text
        if title_index != -1:
            requests += [
                {
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": start_index + title_index, # Start of the heading 
                            "endIndex": start_index + title_index + len(title), # End of the heading 
                        },
                        "paragraphStyle": {"namedStyleType": "HEADING_1"}, # Apply Heading 1 style
                        "fields": "namedStyleType",
                    }
                }
            ]
    
    # Execute the requests to update the headings
    if len(requests) > 0: 
        service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

    # Set the style of the subheadings 
    for x in range(len(subheading_titles)):
        subheading = subheading_titles[x]
        text, start_index, end_index = read_text(service, document_id) # Read the text body to update indices
        title_index = text.find(subheading) # Find the index of the subheading in the text
        
        if title_index != -1:
            newline_index = title_index + start_index + len(subheading) 
            request = [{
                        "insertText": {
                            "location": {
                                "index": newline_index # Insert at the end of the subheading
                            },
                            "text": "\n", #  Insert a new line
                            }, 
                        }, 
                    {
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": title_index + start_index,    # Start of the subheading
                            "endIndex": title_index + start_index + len(subheading), # End of the subheading
                        },
                        "paragraphStyle": {"namedStyleType": "HEADING_3"}, # Apply Heading 3 style
                        "fields": "namedStyleType",
                        }
                    }
                ] 
            service.documents().batchUpdate(documentId=document_id, body={"requests": request}).execute()
                
    # Set the font style of the text 
    requests = [
        {
            "updateTextStyle": {
                "range": {
                    "startIndex": start_index,
                    "endIndex": end_index,
                },
                "textStyle": {
                    "weightedFontFamily": {
                        "fontFamily": "Times New Roman", # Set the font to Times New Roman
                    }
                },
                "fields": "weightedFontFamily",
            }
        }
    ]
    service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

    # Insert page breaks before and after the Executive Summary
    text, start_index, end_index = read_text(service, document_id) # Reread text body to update indicies
    requests = []
    # Find the start and end index of the Executive Summary
    exec_start_index = text.find("Executive Summary")
    exec_end_index = text.find("II. Investment Rationale")
    if exec_start_index > 0:
        requests += [
                    {
                        "insertPageBreak": {
                            "location": {"index": exec_start_index + start_index} # Insert page break before the Executive Summary
                        }
                    }]
    if exec_end_index > 0:
        requests += [
                        { "insertPageBreak": {
                            "location": {"index": exec_end_index + start_index} # Insert page break after the Executive Summary
                        }
                    }
                ]

    service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

    # Insert an image at the beginning of the document
    request = [{ 
        'insertInlineImage': {
            'location': {
                'index': 0
            },
            'uri': 'https://drive.google.com/file/d/1VTHdfG2HbGEg08XdRtYpVlAgGWa9m8IG/view?usp=sharing',
            'objectSize': {
                'height': {
                    'magnitude': 50,
                    'unit': 'PT'
                },
                'width': {
                    'magnitude': 50,
                    'unit': 'PT'
                }
            }
        }
        }
    ]

    service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

    return 


def download_from_drive(drive_service: object, document_id: str, filename: str, 
                        mime_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
    """
    This function downloads a file from Google Drive.
    Args:
        drive_service (googleapiclient.discovery.Resource): The Drive API service.
        document_id (str): The ID of the document to download.
        filename (str): The name of the file to save.
        mime_type (str): The MIME type of the file to download. Defaults to docx type. 
    """
    # Download the file
    download_request = drive_service.files().export(fileId=document_id, mimeType=mime_type)
    download = download_request.execute()

    # Save the file
    with open(filename, "wb") as f:
        f.write(download)

    return 


def format_and_export_memo(filename: str): 
    """ 
    This function formats the memo document and saves it to a docx file in the session state.
    Args:
        filename (str): File name to save memo to. 
    """

    # Set the target scopes 
    target_scopes = ['https://www.googleapis.com/auth/drive.file']

    # Get the source credentials
    source_credentials, _ = google.auth.default()

    # Impersonate the service account
    service_account = os.getenv("SERVICE_ACCOUNT")
    target_credentials = impersonated_credentials.Credentials(
        source_credentials = source_credentials,
        target_principal=service_account,
        target_scopes = target_scopes,
        lifetime=500)

    # Build the Docs and Drive services
    doc_service = build("docs", "v1", credentials=target_credentials)
    drive_service = build("drive", "v3", credentials=target_credentials)

    # Create a new document
    document_id = create_document(service=doc_service, title="memo")

    # Add memo text to the document
    add_text(service=doc_service, document_id=document_id, text=st.session_state.memo_text)

    # Fetch the heading and subheading titles
    heading_titles = fetch_headers("memo_elements/headings.txt")
    subheading_titles = fetch_headers("memo_elements/subheadings.txt")

    # Format the document
    try: 
        format_document(service=doc_service, document_id=document_id, 
                        heading_titles=heading_titles, subheading_titles=subheading_titles)
    except Exception as e:
        st.write("Problem formatting document: ", e)

    # Download the document
    download_from_drive(drive_service=drive_service, document_id=document_id, filename=filename)

    return filename