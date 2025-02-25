import streamlit as st
from gemini_client import create_client, chat_with_model, format_summary_as_markdown
from document_funcs import save_summary_as_docx


def chatbot_tab():
    # Initialize session state variables
    st.session_state.intro_message = {
        "role": "assistant",
        "content": "I am your outline editor assistant!",
        "display_response": "I am your outline editor assistant!",
    }
    if "latest_chatbot_response" not in st.session_state:
        st.session_state.latest_chatbot_response = None
    if "latest_chatbot_display_response" not in st.session_state:
        st.session_state.latest_chatbot_display_response = None

    # Check if a summary has been generated before starting the chat
    if "summary" in st.session_state:
        # Create model clients
        chat_client = create_client(st.session_state.model_option, chatbot=True)
        markdown_client = create_client(st.session_state.model_option)

        # Initialize the chat with an intro message
        if "messages" not in st.session_state:
            st.session_state.messages = [st.session_state.intro_message]

        chat_placeholder = st.container()

        # Display the chat history
        with chat_placeholder:
            for message_index, message in enumerate(st.session_state.messages):
                # Display assistant responses
                if message["role"] == "assistant":
                    if 1 < message_index < len(st.session_state.messages) - 1:
                        # Display previous assistant responses in an expander for readability
                        with st.expander("Assistant Response"):
                            with st.chat_message("assistant"):
                                st.markdown(
                                    message["display_response"], unsafe_allow_html=True
                                )
                    else:
                        # Display the full latest assistant response
                        with st.chat_message("assistant"):
                            st.markdown(
                                message["display_response"], unsafe_allow_html=True
                            )
                # Display user messages
                else:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

        # User chat input
        if prompt := st.chat_input("Enter your message:"):
            st.session_state["messages"].append({"role": "user", "content": prompt})

            # Write user prompt to the chat
            with chat_placeholder:
                with st.chat_message("user"):
                    st.write(prompt)

            # Generate a response from the model
            with chat_placeholder:
                with st.spinner("Generating response..."):
                    response = chat_with_model(
                        model=chat_client,
                        files=st.session_state.files,
                        summary=st.session_state.summary,
                        user_prompt=prompt,
                        msg_history=st.session_state.messages,
                    )

                    display_response = format_summary_as_markdown(
                        markdown_client, summary=response
                    )

                # Save latest responses to the session state
                st.session_state.latest_chatbot_response = response
                st.session_state.latest_chatbot_display_response = display_response

                # Display the response in the chat and save to the chat history
                with st.chat_message("assistant"):
                    st.markdown(
                        st.session_state.latest_chatbot_display_response,
                        unsafe_allow_html=True,
                    )
                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": st.session_state.latest_chatbot_response,
                        "display_response": st.session_state.latest_chatbot_display_response,
                    }
                )

                # Rerun the session to update the chat history
                st.rerun()

        # Clear chat history
        if st.button("Clear chat history"):
            st.session_state["messages"] = [st.session_state.intro_message]
            st.session_state.latest_chatbot_response = None
            st.session_state.latest_chatbot_display_response = None
            st.rerun()

        # Offer download of the latest chatbot response as a docx file
        if st.session_state.latest_chatbot_response is not None:
            # Save the summary as a docx file
            output_path, output_filename = save_summary_as_docx(
                st.session_state.latest_chatbot_response,
                "chatbot_summary.md",
                "chatbot_summary.docx",
            )

            # Display a download button for the docx file
            _ = st.download_button(
                label="Download the latest edit as a docx!",
                data=open(output_path, "rb").read(),
                file_name=output_filename,
            )

    else:
        st.write("Please generate a summary in the Home tab to start chatting.")
