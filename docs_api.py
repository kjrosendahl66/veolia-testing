from googleapiclient.discovery import build
import google.auth
from google.auth import impersonated_credentials
import streamlit as st
import os

def fetch_headers(file): 
    headers = []
    with open(file, "r") as f:
        for line in f:
            headers.append(line.strip())
    return headers

def read_text(service, document_id): 

    document = service.documents().get(documentId=document_id).execute()

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
    end_index = len(text) + start_index
    return text, start_index, end_index

def create_document(service, title):
    body = {
        'title': title} 
    
    doc = service.documents().create(body=body).execute()
    return doc['documentId']

def add_text(service, document_id, text): 
    requests = [
                {
                    "insertText": {
                        "location": {"index": 1},  # Insert at the beginning
                        "text": text,
                    }
                }
            ]

    body = {"requests": requests}
    service.documents().batchUpdate(documentId=document_id, body=body).execute()

def format_document(service, document_id, heading_titles, subheading_titles):

    text, start_index, end_index = read_text(service, document_id)
    requests = []
    for title in heading_titles:
        title_index = text.find(title) 
        if title_index != -1:
            requests += [
                {
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": start_index + title_index,
                            "endIndex": start_index + title_index + len(title),
                        },
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "fields": "namedStyleType",
                    }
                }
            ]

    service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

    # requests = [] 
    for x in range(len(subheading_titles)):
        subheading = subheading_titles[x]
        text, start_index, end_index = read_text(service, document_id)
        title_index = text.find(subheading)
        if title_index != -1:
            newline_index = title_index + start_index + len(subheading)
            request = [{
                        "insertText": {
                            "location": {
                                "index": newline_index
                            },
                            "text": "\n",
                            }, 
                        }, 
                    {
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": title_index + start_index,
                            "endIndex": title_index + start_index + len(subheading),
                        },
                        "paragraphStyle": {"namedStyleType": "HEADING_3"},
                        "fields": "namedStyleType",
                        }
                    }
                ] 
            service.documents().batchUpdate(documentId=document_id, body={"requests": request}).execute()
                
    # Set the paragraph style of all the text to normal text:
    requests = [
        {
            "updateTextStyle": {
                "range": {
                    "startIndex": start_index,
                    "endIndex": end_index,
                },
                "textStyle": {
                    "weightedFontFamily": {
                        "fontFamily": "Times New Roman",
                    }
                },
                "fields": "weightedFontFamily",
            }
        }
    ]
    service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()


    text, start_index, end_index = read_text(service, document_id)
    requests = []
    exec_start_index = text.find("Executive Summary")
    exec_end_index = text.find("II. Investment Rationale")
    if exec_start_index > 0:
        requests += [
                    {
                        "insertPageBreak": {
                            "location": {"index": exec_start_index + start_index}
                        }
                    }]
    if exec_end_index > 0:
        requests += [
                        { "insertPageBreak": {
                            "location": {"index": exec_end_index + start_index}
                        }
                    }
                ]

    service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

    

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


def download_from_drive(drive_service, document_id, filename, mime_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
    download_request = drive_service.files().export(fileId=document_id, mimeType=mime_type)
    download = download_request.execute()
    with open(filename, "wb") as f:
        f.write(download)
    return 


def format_and_export_memo(): 

    target_scopes = ['https://www.googleapis.com/auth/drive.file']
    source_credentials, project = google.auth.default()

    service_account = os.getenv("SERVICE_ACCOUNT")

    target_credentials = impersonated_credentials.Credentials(
        source_credentials = source_credentials,
        target_principal=service_account,
        target_scopes = target_scopes,
        lifetime=500)

    doc_service = build("docs", "v1", credentials=target_credentials)
    drive_service = build("drive", "v3", credentials=target_credentials)

    # Create a new document
    document_id = create_document(doc_service, "memo")

    add_text(doc_service, document_id, st.session_state.memo_text)

    heading_titles = fetch_headers("memo_elements/headings.txt")
    subheading_titles = fetch_headers("memo_elements/subheadings.txt")

    try: 
        format_document(doc_service, document_id, heading_titles, subheading_titles)
    except Exception as e:
        st.write("Problem formatting document: ", e)

    filename = 'memo.docx'
    download_from_drive(drive_service, document_id, filename)

    return filename