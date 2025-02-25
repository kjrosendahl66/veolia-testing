import vertexai
from vertexai.generative_models import GenerativeModel, Part
from vertexai.preview import caching
from google.genai.types import GenerateContentConfig
from google.genai import types

CHATBOT_SYSTEM_INSTRUCTIONS = """
        You are a chatbot model responsible for editing a generated summary outline given documents. 
        You will be given files which contain the original document and the desired outline. 
        You will also be given a generated summary outline.
        You will also have the conversation history.
        Make edits and improvements to the generated summary outline based on the user input. 
        Still include the outline fields, structure, and page numbers when appropriate.
        """

# Create a client for the Generative Model
def create_client(model_name="gemini-1.5-pro", chatbot = False):
    if chatbot:
        return GenerativeModel(model_name, system_instruction=CHATBOT_SYSTEM_INSTRUCTIONS) 
    return GenerativeModel(model_name)

def load_part_from_gcs(files: dict, mime_type: str = "application/pdf"):

    lst_pdf_files = []

    for _, file_locations in files.items():
        pdf_file = Part.from_uri(
            uri=file_locations["gcs_file_location"],
            mime_type=mime_type
        )
        lst_pdf_files.append(pdf_file)

    return lst_pdf_files

def summarize_cim(model, files: dict, mime_type: str = "application/pdf", temperature: float = .7):

    """
    This function uses Gemini to generate a summary of a CIM using an outline template. 
    Both the CIM and the template are provided as PDF files, uploaded to GCS. 
    Args: 
        model (GemerativeModel): A GenerativeModel object. 
        files (dict): A dictionary containing the file locations of the CIM and the template
        mime_type (str, optional): The mime type of the files
        temperature (float, optional): The temperature for the model generation. 
    Returns: 
        A string containing the generated summary.
    """
    
    prompt = """
    Fill in the following template with the information in the provided document. Be detailed.
    The output should have detailed metrics and statistics extracted from the document when appropriate. 
    If the information cannot be concluded from the provided sample, leave the field blank. 
    Include page numbers for references for each section.
    """
    # Return an organized output as multiple tables.

    contents = [prompt] 

    # Add the PDF files to the contents
    contents += load_part_from_gcs(files, mime_type=mime_type)

    generation_config = {"temperature": temperature}

    # Generate the response
    response = model.generate_content(contents=contents, generation_config=generation_config)
    return response.text


def format_summary_as_markdown(model, summary: str, temperature: float = .7):
    """
    This function formats a summary generated by the Generative Model into multiple markdown tables.
    Args:
        model (GemerativeModel): A GenerativeModel object. 
        summary (str): The generated CIM summary. 
        temperature (float, optional): The temperature for the model generation.
    Returns: 
        A string containing the formatted summary in markdown format.
    """

    prompt = """
    Format the following summary into multiple markdown tables. 
    The output should be in markdown format. The columns should be field, value/description, and page numbers. 
    It should be neat, readable, and not verbose. 
    Include page numbers where info was found as another column.
    """

    contents = [prompt, summary] 

    # Set the generation config
    generation_config = {"temperature": temperature}

    # Generate the response
    response = model.generate_content(contents=contents, generation_config=generation_config)
    return response.text

def format_chat_history(msg_history: list) -> list[str]:
    """
    Formats the chat history (list of dictionaries) into a list of strings for the LLM.
    Args:
        msg_history (list): A list of dictionaries, where each dictionary has 'role' and 'content'.
    Returns:
        list[str]: A list of strings representing the conversation turns.
    """
    formatted_history = []
    for msg in msg_history:
        formatted_history.append(f"{msg['role']}: {msg['content']}")
    return formatted_history

def chat_with_model(model: GenerativeModel, 
                    files: dict, 
                    summary: str, 
                    user_prompt: str, 
                    msg_history: list, 
                    mime_type: str = "application/pdf", 
                    temperature: float = .7):
    
    # Add the PDF files to the contents
    contents = load_part_from_gcs(files, mime_type=mime_type)
    contents += [summary, user_prompt]

    # Format the chat history
    formatted_history = format_chat_history(msg_history)
    contents += formatted_history
    
    generation_config = {"temperature": temperature}

    # Generate the response
    response = model.generate_content(contents=contents, generation_config=generation_config)
    return response.text