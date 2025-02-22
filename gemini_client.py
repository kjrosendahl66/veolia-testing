import vertexai
from vertexai.generative_models import GenerativeModel, Part


# Create a client for the Generative Model
def create_client(project_id, location, model_name="gemini-1.5-pro-002"): 
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel(model_name)
    return model 

def summarize_cim(model, file_uri, outline_uri, mime_type: str = "application/pdf"):

    prompt = """
    Fill in the following template with the information in the provided document. Be detailed.
    The output should have detailed metrics and statistics extracted from the document when appropriate. 
    If the information cannot be concluded from the provided sample, leave the field blank. 
    Return an organized output as multiple tables. 
    """

    pdf_file = Part.from_uri(
        uri=file_uri,
        mime_type=mime_type
    )

    pdf_outline = Part.from_uri(
        uri = f"{outline_uri}",
        mime_type = "application/pdf"
    )
    contents = [pdf_file, pdf_outline, prompt]

    response = model.generate_content(contents)
    return response.text
