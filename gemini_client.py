from vertexai.generative_models import GenerativeModel, Part
from typing import Dict, List

# Define the system instructions for the chatbot
EDITOR_SYSTEM_INSTRUCTIONS = """
        You are a chatbot model responsible for editing a generated summary outline given documents. 
        You will be given files which contain the original document and the desired outline. 
        You will also be given a generated summary outline.
        You will also have the conversation history.
        Make edits and improvements to the generated summary outline based on the user input. 
        Still adhere to the outline template, outline fields, and page numbers. 
        If the information cannot be concluded, label the field as "Not Available".
        """

QA_SYSTEM_INSTRUCTIONS = """
    You are a chatbot model responsible for answering questions about a given document.
    You will be given files which contain the original documents.
    You will also have the conversation history. 
    Answer the user prompt based on the information in the document. 
    Be friendly and helpful. Include page numbers for references.
    """

# Create a client for the Generative Model
def create_client(model_name: str = "gemini-2.0-flash", chatbot_function: str = None):
    if chatbot_function == "editor":
        return GenerativeModel(
            model_name, system_instruction=EDITOR_SYSTEM_INSTRUCTIONS
        )
    
    elif chatbot_function == "qa":
        return GenerativeModel(
            model_name, system_instruction=QA_SYSTEM_INSTRUCTIONS
        )
    
    return GenerativeModel(model_name)


def load_part_from_gcs(
    files: Dict[str, Dict[str, str]]
):
    """
    This function loads the PDF files from GCS and returns a list of Part objects for the LLM.
    """

    lst_pdf_files = []

    for _, file_locations in files.items():
        pdf_file = Part.from_uri(
            uri=file_locations["gcs_file_location"], mime_type=file_locations["mime_type"]
        )
        lst_pdf_files.append(pdf_file)

    return lst_pdf_files


def summarize_cim(
    model,
    files: Dict[str, Dict[str, str]],
    temperature: float = 0.7,
):
    """
    This function uses Gemini to generate a summary of a CIM using an outline template.
    Both the CIM and the template are provided as PDF files, uploaded to GCS.
    Args:
        model (GemerativeModel): A GenerativeModel object.
        files (dict): A dictionary containing the file locations of the CIM and the template
        temperature (float, optional): The temperature for the model generation.
    Returns:
        A string containing the generated summary.
    """

    prompt = """
    Fill in the following template with the information in the provided document. Be detailed.
    The output should have detailed metrics and statistics extracted from the document when appropriate. 
    If the information cannot be concluded from the provided sample, label the field as "Not Available".
    Include page numbers for references for each section.
    """

    contents = [prompt]

    # Add the PDF files to the contents
    contents += load_part_from_gcs(files)

    generation_config = {"temperature": temperature}

    # Generate the response
    response = model.generate_content(
        contents=contents, generation_config=generation_config
    )
    return response.text


def format_summary_as_markdown(model, summary: str, temperature: float = 0.7):
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
    The output should be in markdown format. 
    Nest information in a table or create multiple columns if appropriate.
    It should be neat, readable, and not verbose. 
    Include page numbers where info was found as another column.
    """

    contents = [prompt, summary]

    # Set the generation config
    generation_config = {"temperature": temperature}

    # Generate the response
    response = model.generate_content(
        contents=contents, generation_config=generation_config
    )
    return response.text


def format_chat_history(msg_history: List[Dict[str, str]]) -> list[str]:
    """
    Formats the chat history (list of dictionaries) into a list of strings for the LLM.
    Args:
        msg_history (list): A list of dictionaries, where each dictionary has 'role', 'content', and optionally 'display_response' keys.
    Returns:
        list[str]: A list of strings representing the conversation turns.
    """
    formatted_history = []
    for msg in msg_history:
        formatted_history.append(f"{msg['role']}: {msg['content']}")
    return formatted_history


def chat_with_model(
    model: GenerativeModel,
    files: Dict[str, Dict[str, str]],
    user_prompt: str,
    msg_history: List[Dict[str, str]],
    summary: str = None,
    temperature: float = 0.7,
):
    """
    This function uses Gemini to generate a response to a user prompt based on the provided files and chat history.

    Args:
        model (GemerativeModel): A GenerativeModel object.
        files (dict): A dictionary containing the file locations of the CIM and the template.
        user_prompt (str): The user input.
        msg_history (list): A list of dictionaries representing the chat history.
        summary (str, optional): The previous summary, if using editor chatbot.
        temperature (float, optional): The temperature for the model generation. Defaults to .7.
    Returns:
       Response: A string containing the generated response.    
    """

    # Add the PDF files to the contents
    contents = load_part_from_gcs(files)
    contents += [user_prompt]
    if summary:
        contents += [summary]

    # Format the chat history
    formatted_history = format_chat_history(msg_history)
    contents += formatted_history

    generation_config = {"temperature": temperature}

    # Generate the response
    response = model.generate_content(
        contents=contents, generation_config=generation_config
    )
    return response.text
