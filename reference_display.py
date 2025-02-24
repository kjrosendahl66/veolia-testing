
import streamlit as st 
def display_page(doc):

    page = doc.load_page(st.session_state.get("current_page",1) - 1)
    st.image(page.get_svg_image())
    st.caption(f"Page {st.session_state.get('current_page',1)} of {doc.page_count}")

def navigation_buttons(doc):
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

    with col_nav1:
        if st.session_state.get("current_page",1) > 1:
            st.write("\n")
            if st.button("Previous Page", key="prev_button"):
                st.session_state["current_page"] -= 1
                st.rerun()

    with col_nav2:
        if 1 <= st.session_state.get("current_page",1) <= doc.page_count:
            page_number = st.selectbox("Jump to page:", options=range(1, doc.page_count + 1),
                                        index=st.session_state.get("current_page", 1) - 1,  # Show current page
                                        key="page_selectbox" # Added key so that this reruns on value change.
            )
            if page_number != st.session_state.get("current_page", 1):
                st.session_state["current_page"] = page_number
                st.rerun()

    with col_nav3:
      if st.session_state.get("current_page",1) < doc.page_count:
        st.write("\n")
        if st.button("Next Page", key="next_button"):
            st.session_state["current_page"] += 1
            st.rerun()

def render_files():
    if st.session_state.files: 
        file_names = list(st.session_state.files.keys())

        file_option = st.selectbox("Select a file to view", options=file_names, index=0)
        if file_option:

           #Reset the page when file is changed.
            if "last_selected_file" not in st.session_state:
                st.session_state.last_selected_file = file_option
                st.session_state.current_file = st.session_state.docs[file_option]
                st.session_state.current_page = 1
            elif st.session_state.last_selected_file != file_option:
                st.session_state.last_selected_file = file_option
                st.session_state.current_file = st.session_state.docs[file_option]
                st.session_state.current_page = 1

            doc = st.session_state.docs[file_option]
            navigation_buttons(doc)
            display_page(doc)