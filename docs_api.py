from googleapiclient.discovery import build
import google.auth
from google.auth import impersonated_credentials
import streamlit as st
import os

TAB_TITLES = ["Executive Summary", 
              "II. Investment Rationale", 
              "III. About the Target", 
              "IV. Growth Opportunity", 
              "V. Key Financial Model Assumptions", 
              "VI. Preliminary Integration Plan", 
              "VII. Legal and Contractual Analysis",
              "VIII. Preliminary Risk Analysis and Due Diligence Plan",
              "Appendices"]

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


def format_document(service, document_id, text, start_index, end_index, tab_titles): 

    requests = [] 
    
    for title in tab_titles:
        title_index = text.find(title)
        if title_index != -1:
            actual_title_index = title_index + start_index
                        
            requests.append(
                {
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": actual_title_index,
                            "endIndex": actual_title_index + len(title),
                        },
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "fields": "namedStyleType",
                    }
                }
            )

    # Set the paragraph style of all the text to normal text:
    requests.append(
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
    )

    #insert page break before the header if its not the first header.
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
        
        # Add bullets to paragraphs
    paragraphs = text.split("\n")
    current_index = start_index
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph and paragraph not in tab_titles:
            # Check if it is not just whitespace and not a title
            requests.append(
                {
                    "createParagraphBullets": {
                        "range": {
                            "startIndex": current_index,
                            "endIndex": current_index + len(paragraph),
                        },
                        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                    }
                }
            )
        current_index += len(paragraph) + 1


    service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
    return 


def download_from_drive(drive_service, document_id, filename, mime_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
    download_request = drive_service.files().export(fileId=document_id, mimeType=mime_type)
    download = download_request.execute()
    with open(filename, "wb") as f:
        f.write(download)
    return 


def export_memo(): 

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
    text, start_index, end_index = add_text(doc_service, document_id, st.session_state.memo_text)

    format_document(doc_service, document_id, text, start_index, end_index, TAB_TITLES)

    filename = 'memo.docx'
    download_from_drive(drive_service, document_id, filename)

    _ = st.download_button(
        label=f"Download memo as formatted docx",
        data=open(filename, "rb").read(),
        file_name=filename,
    )
