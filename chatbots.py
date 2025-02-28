import streamlit as st
from gemini_client import create_client, chat_with_model, format_summary_as_markdown
from document_funcs import display_download_buttons
from utils import render_markdown


def editor_chabot():

    """
    This function displays the editor chatbot interface in Streamlit.
    The chatbot reads the session files and summary generated in the Home tab. 
    Users may ask the bot to refine the summary by making requested edits.
    Chat history and updated summaries are displayed in the interface.
    Users have the options to download the latest edited summary and clear the chat history.
    """
    
    # Initialize session state variables
    st.session_state.editor_intro_msg = {
        "role": "assistant",
        "content": "I am your editor assistant! Request edits and refine your summary! 📝",
        "display_response": "I am your editor assistant! Request edits and refine your summary! 📝",
    }

    if "latest_editor_chatbot_response" not in st.session_state:
        st.session_state.latest_editor_chatbot_response = None

    if "editor_messages" not in st.session_state:
        st.session_state.editor_messages = [st.session_state.editor_intro_msg]

    # Init model for editor chatbot 
    editor_chat_client = create_client(
        st.session_state.model_option, chatbot_function="editor"
    )

    editor_chat_placeholder = st.container()

    # Display chat history
    with editor_chat_placeholder:
        for message_index, message in enumerate(st.session_state.editor_messages):
            # Display assistant responses
            if message["role"] == "assistant":
                if 1 < message_index < len(st.session_state.editor_messages) - 1:
                    # Display previous assistant responses in an expander for readability
                    with st.expander("Assistant Response"):
                        with st.chat_message("assistant"):
                            st.markdown(
                                render_markdown(message["display_response"]),
                                unsafe_allow_html=True,
                            )
                else:
                    # Display the full latest assistant response
                    with st.chat_message("assistant"):
                        st.markdown(
                            render_markdown(message["display_response"]),
                            unsafe_allow_html=True,
                        )
            # Display user messages
            else:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

    # User chat input
    if prompt := st.chat_input("Enter your requested edits:"):
        st.session_state["editor_messages"].append({"role": "user", "content": prompt})

        # Write user prompt to the chat
        with editor_chat_placeholder:
            with st.chat_message("user"):
                st.write(prompt)

        with editor_chat_placeholder:
            with st.spinner("Generating response..."):
                # Send request to the editor chatbot
                editor_response = chat_with_model(
                    model=editor_chat_client,
                    files=st.session_state.files,
                    summary=st.session_state.summary,
                    user_prompt=prompt,
                    msg_history=st.session_state.editor_messages,
                )

                # Format the response for display in the chat
                editor_display_response = format_summary_as_markdown(
                    st.session_state.markdown_gemini_client, summary=editor_response
                )

            # Display the response in the chat 
            with st.chat_message("assistant"):
                st.markdown(
                    render_markdown(editor_display_response),
                    unsafe_allow_html=True,
                )

            # Save the response to the chat history
            st.session_state["editor_messages"].append(
                {
                    "role": "assistant",
                    "content": editor_response,
                    "display_response": editor_display_response,
                }
            )
            
            # Save the latest response for edited summary download
            st.session_state.latest_editor_chatbot_response = editor_response

            # Rerun the session to update the chat history
            st.rerun()

    # Clear chat history and reset intro message
    if st.button("Clear chat history", key="clear_editor_chat_history"):
        st.session_state["editor_messages"] = [st.session_state.editor_intro_msg]
        st.session_state.latest_editor_chatbot_response = None
        st.rerun()

    st.divider()

    # Offer download of the latest chatbot response
    if st.session_state.latest_editor_chatbot_response is not None:
        display_download_buttons(summary_name="chatbot_summary")


# -------------------------------------------------


def qa_chatbot():

    """
    This function displays the Q&A chatbot interface in Streamlit.
    The chatbot reads the session files and allows users to ask questions about the documents.
    Chat history and responses are displayed in the interface.
    """

    # Initialize session state variables
    st.session_state.qa_intro_msg = {
        "role": "assistant",
        "content": "I am your Q&A assistant! Ask me questions about your documents! 🤖",
    }

    if "qa_messages" not in st.session_state:
        st.session_state.qa_messages = [st.session_state.qa_intro_msg]

    # Init model for Q&A chatbot
    qa_chat_client = create_client(st.session_state.model_option, chatbot_function="qa")

    qa_chat_placeholder = st.container()

    # Display chat history
    with qa_chat_placeholder:
        for message in st.session_state.qa_messages:
            # Display assistant messages
            if message["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(
                        render_markdown(message["content"]), unsafe_allow_html=True
                    )
            # Display user messages
            else:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

    # User chat input
    if prompt := st.chat_input("Enter your question:"):
        st.session_state["qa_messages"].append({"role": "user", "content": prompt})

        # Write user prompt to the chat
        with qa_chat_placeholder:
            with st.chat_message("user"):
                st.write(prompt)

        with qa_chat_placeholder:
            # Generate response
            with st.spinner("Generating response..."):
                qa_response = chat_with_model(
                    model=qa_chat_client,
                    files=st.session_state.files,
                    user_prompt=prompt,
                    msg_history=st.session_state.qa_messages,
                )

            # Display the response in the chat
            with st.chat_message("assistant"):
                st.markdown(
                    render_markdown(qa_response),
                    unsafe_allow_html=True,
                )

            # Save the response to the chat history
            st.session_state["qa_messages"].append(
                {
                    "role": "assistant",
                    "content": qa_response,
                }
            )

            # Rerun the session to update the chat history
            st.rerun()

    # Clear chat history and reset intro message
    if st.button("Clear chat history", key="clear_qa_chat_history"):
        st.session_state["qa_messages"] = [st.session_state.qa_intro_msg]
        st.rerun()
