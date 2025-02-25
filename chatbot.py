import streamlit as st 
from gemini_client import create_client, chat_with_model, format_summary_as_markdown
from document_funcs import save_summary_as_docx

def chatbot_tab(): 

    # Initialize session state
    st.session_state.intro_message = {
        'role': 'assistant', 
        'content': "I am your outline editor assistant!", 
        'display_response': "I am your outline editor assistant!"
    }
    if "latest_chatbot_response" not in st.session_state:
        st.session_state.latest_chatbot_response = None
    if "latest_chatbot_display_response" not in st.session_state:
        st.session_state.latest_chatbot_display_response = None


    if "summary" in st.session_state:
        chat_client = create_client(st.session_state.model_option, chatbot = True)
        markdown_client = create_client(st.session_state.model_option)
        
        if "messages" not in st.session_state:
            st.session_state.messages = [st.session_state.intro_message]
        
        chat_placeholder = st.container() 
        with chat_placeholder:
            for message_index, message in enumerate(st.session_state.messages):
                if message["role"] == "assistant":
                    if 1 < message_index < len(st.session_state.messages) - 1:
                        with st.expander("Assistant Response"):
                            with st.chat_message("assistant"): 
                                st.markdown(message["display_response"], unsafe_allow_html=True)
                    else: 
                        with st.chat_message("assistant"):
                            st.markdown(message["display_response"], unsafe_allow_html=True)
                else: 
                    with st.chat_message(message["role"]): 
                        st.write(message["content"])
                    
        if prompt := st.chat_input("Enter your message:"):
            st.session_state['messages'].append({'role': 'user', 'content': prompt})
            with chat_placeholder: 
                with st.chat_message('user'): 
                    st.write(prompt)
            with chat_placeholder:
                with st.spinner("Generating response..."):
                    response = chat_with_model(
                                            model = chat_client, 
                                            files = st.session_state.files, 
                                            summary = st.session_state.summary, 
                                            user_prompt = prompt, 
                                            msg_history = st.session_state.messages)
                    
                    display_response = format_summary_as_markdown(markdown_client, summary = response)

                st.session_state.latest_chatbot_response = response 
                st.session_state.latest_chatbot_display_response = display_response

                with st.chat_message('assistant'): 
                    st.markdown(st.session_state.latest_chatbot_display_response, unsafe_allow_html=True)

                st.session_state['messages'].append({'role': 'assistant', 'content': st.session_state.latest_chatbot_response, 
                                                    'display_response': st.session_state.latest_chatbot_display_response}) 
                st.rerun()
        
        # st.button("Clear chat history", on_click=clear_history)
        if st.button("Clear chat history"):
            st.session_state['messages'] = [st.session_state.intro_message]
            st.session_state.latest_chatbot_response = None
            st.session_state.latest_chatbot_display_response = None
            st.rerun()

        if st.session_state.latest_chatbot_response is not None:
            # Save the summary as a docx file
            output_path, output_filename = save_summary_as_docx(st.session_state.latest_chatbot_response,"chatbot_summary.md", "chatbot_summary.docx")

            # Display a download button for the docx file
            download = st.download_button(
                label="Download the latest edit as a docx!",
                data=open(output_path, "rb").read(),
                file_name=output_filename,
            )

    else: 
        st.write("Please generate a summary in the Home tab to start chatting.")

