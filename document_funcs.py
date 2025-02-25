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
        file_names = list(st.session_state.files.keys())
        file_option = st.selectbox("Select a file to view", options=file_names, index=0)

        if file_option:
            # Load the selected file
            if "last_selected_file" not in st.session_state:
                st.session_state.last_selected_file = file_option
                st.session_state.current_file = st.session_state.docs[file_option]
                st.session_state.current_page = 1
            # Update the selected file when option is changed
            elif st.session_state.last_selected_file != file_option:
                st.session_state.last_selected_file = file_option
                st.session_state.current_file = st.session_state.docs[file_option]
                st.session_state.current_page = 1

            # Load the document and display the page
            doc = st.session_state.docs[file_option]
            navigation_buttons(doc)
            display_page(doc)


def save_summary_as_docx(
    summary: str,
    summary_filename: str = "summary.md",
    output_filename: str = "summary.docx",
):
    """
    This function saves a summary as a docx file for user download.
    """

    # Construct path
    summary_path = os.path.join(st.session_state.temp_dir, summary_filename)
    output_path = os.path.join(st.session_state.temp_dir, output_filename)

    # Save the summary to a local path
    with open(summary_path, "w") as f:
        f.write(summary)

    # Convert the summary to a docx file
    pypandoc.convert_file(summary_path, "docx", outputfile=output_path)

    return output_path, output_filename
