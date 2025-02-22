import vertexai
from vertexai.generative_models import GenerativeModel, Part


# Create a client for the Generative Model
def create_client(project_id, location, model_name="gemini-1.5-pro-002"): 
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel(model_name)
    return model 

def summarize_cim(model, file_locations: list[str], mime_type: str = "application/pdf"):

    prompt = """
    Fill in the following template with the information in the provided document. Be detailed.
    The output should have detailed metrics and statistics extracted from the document when appropriate. 
    If the information cannot be concluded from the provided sample, leave the field blank. 
    Return an organized output as multiple tables. 
    """

    contents = [prompt] 

    for file in file_locations:
        pdf_file = Part.from_uri(
            uri=file,
            mime_type=mime_type
        )
        contents.append(pdf_file)

    response = model.generate_content(contents)
    return response.text
