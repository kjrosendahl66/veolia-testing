import streamlit as st
import os
import pypandoc


def display_page(doc):
    """
    This function displays a page of a document.
    """

    # Load the page
    page = doc.load_page(st.session_state.get("current_page", 1) - 1)
    # Display the page
    st.image(page.get_svg_image())
    st.caption(f"Page {st.session_state.get('current_page',1)} of {doc.page_count}")


def navigation_buttons(doc):
    """
    This function displays the navigation buttons for the document viewer.
    """

    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

    # Button for previous page
    with col_nav1:
        # Display button for all pages except the first
        if st.session_state.get("current_page", 1) > 1:
            st.write("\n")
            # Update page and rerun session
            if st.button("Previous Page", key="prev_button"):
                st.session_state["current_page"] -= 1
                st.rerun()

    # Select box for jumping to a specific page
    with col_nav2:
        if 1 <= st.session_state.get("current_page", 1) <= doc.page_count:
            # Display all page numbers
            page_number = st.selectbox(
                "Jump to page:",
                options=range(1, doc.page_count + 1),
                index=st.session_state.get("current_page", 1) - 1,  # Show current page
                key="page_selectbox",
            )

            # Jump to the selected page and update page and session
            if page_number != st.session_state.get("current_page", 1):
                st.session_state["current_page"] = page_number
                st.rerun()

    # Button for next page
    with col_nav3:
        # Display button for all pages except the last
        if st.session_state.get("current_page", 1) < doc.page_count:
            st.write("\n")
            # Update page and rerun session
            if st.button("Next Page", key="next_button"):
                st.session_state["current_page"] += 1
                st.rerun()


def render_files():
    """
    This function renders the uploaded files in the file viewer.
    """

    # Display the file viewer with uploaded files
    if st.session_state.files:

        # Display the file selection dropdown
        file_names = list(st.session_state.files.keys())
        file_option = st.selectbox("Select a file to view", options=file_names, index=0)

        if file_option:
            # Load the selected file
            if "last_selected_file" not in st.session_state:
                st.session_state.last_selected_file = file_option
                # st.session_state.current_file = st.session_state.docs[file_option]
                st.session_state.current_file = st.session_state.files[file_option]["doc"]
                st.session_state.current_page = 1
            # Update the selected file when option is changed
            elif st.session_state.last_selected_file != file_option:
                st.session_state.last_selected_file = file_option
                st.session_state.current_file = st.session_state.files[file_option]["doc"]
                # st.session_state.current_file = st.session_state.docs[file_option]
                st.session_state.current_page = 1

            # Load the document and display the page
            # doc = st.session_state.docs[file_option]
            doc = st.session_state.files[file_option]["doc"]
            navigation_buttons(doc)
            display_page(doc)


def save_summary_as_docx(summary: str, summary_filename: str, output_filename: str): 
    """
    This function saves a chatbot/generated summary as a docx file.
    """

    # Construct path
    summary_path = os.path.join(st.session_state.temp_dir, summary_filename)
    output_path = os.path.join(st.session_state.temp_dir, output_filename)

    # Save the summary to a local path
    with open(summary_path, "w") as f:
        for line in summary.split("\n"):
            f.write(line + "\n")

    # Convert to docx
    pypandoc.convert_file(summary_path, "docx", outputfile=output_path)

    return output_path, output_filename

def convert_docx_to_pdf(docx_path: str, output_pdf_filename:str):
    """
    This function converts a docx file to a pdf file.
    """
    output_path = os.path.join(st.session_state.temp_dir, output_pdf_filename)
    pypandoc.convert_file(docx_path, "pdf", outputfile=output_path, extra_args=['-V geometry:margin=1.5cm', '--pdf-engine=pdflatex'])

    return output_path, output_pdf_filename


def display_download_buttons(summary_name: str ="summary"):
        """
        This function displays buttons for downloading a summary as a docx, pdf, or txt.
        """

        # Determine the summary content and button text based on the summary name
        if summary_name == "summary": 
            summary_content = st.session_state.summary 
            button_display_text = "Download summary" 

        elif summary_name == "chatbot_summary":
            summary_content = st.session_state.latest_editor_chatbot_response
            button_display_text = "Download the latest edit"

        # Save the summary as a docx file
        try: 
            docx_output_path, docx_output_filename = save_summary_as_docx(
                summary_content, f"{summary_name}.md", f"{summary_name}.docx"
            )
        except Exception as e: 
            st.error(f"Error saving as a docx file: {e}")
            docx_output_path, docx_output_filename = None, None

        # Save the summary as a pdf file using the docx file
        try: 
            pdf_output_path, pdf_output_filename = convert_docx_to_pdf(
                docx_output_path, f"{summary_name}.pdf"
            )
        except Exception as e: 
            st.error(f"Error saving as a pdf file: {e}")
            pdf_output_path, pdf_output_filename = None, None

        # Display download buttons
        col1, col2, col3 = st.columns(3)

        # Download button for docx
        with col1: 
            if docx_output_path is not None and docx_output_filename is not None:              
                _ = st.download_button(
                    label=f"{button_display_text} as a docx!",
                    data=open(docx_output_path, "rb").read(),
                    file_name=docx_output_filename,
                )
        # Download button for pdf
        with col2:
            if pdf_output_path is not None and pdf_output_filename is not None:
                _ = st.download_button(
                    label=f"{button_display_text} as a pdf!",
                    data=open(pdf_output_path, "rb").read(),
                    file_name=pdf_output_filename,
                )
        # Download button for txt
        with col3: 
            _ = st.download_button(
                label=f"{button_display_text} as a txt!",
                data=summary_content,
                file_name=f"{summary_name}.txt",
            )