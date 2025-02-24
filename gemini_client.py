import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
import json

# Create a client for the Generative Model
def create_client(project_id, location, model_name="gemini-1.5-pro"): 
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel(model_name)
    return model 

def summarize_cim(model, files: dict, mime_type: str = "application/pdf", temperature: float = .7):
    prompt = """
    Fill in the following template with the information in the provided document. Be detailed.
    The output should have detailed metrics and statistics extracted from the document when appropriate. 
    If the information cannot be concluded from the provided sample, leave the field blank. 
    Return an organized output as multiple tables. Include page numbers where info was found as another column.
    """

    # Return an organized output JSON with markdown formatting. 
    # For each field, provide the extracted information and the page numbers where it was found as an array./
    # Use this schema: 
    # {'section': {'field': {'value': str, 'pages': list[int]}, 'field': {'value': str, 'pages': list[int]}, ...},
    # ...} 

    contents = [prompt] 

    for file_name, file_locations in files.items():
        pdf_file = Part.from_uri(
            uri=file_locations["gcs_file_location"],
            mime_type=mime_type
        )
        contents.append(pdf_file)

    generation_config = {"temperature": temperature}

    response = model.generate_content(contents=contents, generation_config=generation_config)
    return response.text
