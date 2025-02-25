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
    Include page numbers for references for each section.
    """

    # Return an organized output as multiple tables.

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

def format_summary_as_markdown(model, summary: str, temperature: float = .7):
    prompt = """
    Format the following summary into multiple markdown tables. 
    The output should be in markdown format. The columns should be field, value/description, and page numbers. 
    It should be neat, readable, and not verbose. 
    Include page numbers where info was found as another column.
    """

    contents = [prompt, summary] 

    generation_config = {"temperature": temperature}

    response = model.generate_content(contents=contents, generation_config=generation_config)
    return response.text