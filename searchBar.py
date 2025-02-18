import os
import streamlit as st
from dotenv import load_dotenv
from functions.product_details import product_images
from functions.doc_processor import get_pdf_texts, create_knowledge_hub
from functions.dynamix_processor import (
    get_autocomplete_suggestions,
    update_autocomplete,
    generate_knowledge_answer
)
from services.constants import CANPREV_IMAGE_PATH

load_dotenv(override=True)


def main():
    st.set_page_config(page_title="Product Q&A", page_icon="🍲", layout="wide")

    # Sidebar: About and Knowledge Base update.
    with st.sidebar:
        st.image(CANPREV_IMAGE_PATH, width=200)
        st.markdown("## About Canprev")
        st.markdown(
            """
            **Canprev** is a leading provider of innovative health and wellness products.  
            Our research-backed formulations are designed to help you achieve your health goals.  
            Explore our products and feel free to ask any questions about them!
            """
        )
        st.markdown("---")
        if st.button("Build/Update Knowledge Base",type="primary"):
            with st.spinner("Building the knowledge base from PDF files..."):
                documents = get_pdf_texts()
                create_knowledge_hub(documents)
                st.success("Knowledge Base updated successfully!")

    # Main title and instructions.
    st.title("Product Q&A ")
    st.markdown(
        "Ask a question about our products...."
    )

    # Set up the text input.
    if "user_query" not in st.session_state:
        st.session_state.user_query = ""
    user_query = st.text_input(
        "Search:",
        key="user_query",
        value=st.session_state.user_query,
        placeholder="Type your question here...",
        on_change=update_autocomplete,
    )

    # Get autocomplete suggestions if the query is at least 3 characters.
    suggestions = (
        get_autocomplete_suggestions(user_query)
        if user_query and len(user_query) >= 3
        else []
    )
    if suggestions:
        st.markdown("**Suggestions:**")
        for suggestion in suggestions:
            if st.button(suggestion, key=suggestion,type="primary"):
                with st.spinner("Thinking..."):
                    answer_response = generate_knowledge_answer(suggestion)
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []
                st.session_state.chat_history.append(
                    {"role": "user", "content": suggestion}
                )
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer_response.get("output", "")}
                )

    # Ensure conversation history exists.
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # When the user clicks "Submit Query".
    if st.button("Submit",type="primary"):
        if user_query:
            with st.spinner("Thinking..."):
                answer_response = generate_knowledge_answer(user_query)
            st.session_state.chat_history.append(
                {"role": "user", "content": user_query}
            )
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer_response.get("output", "")}
            )

    # Display conversation messages.
    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("Conversation")
        # Display messages as pairs (user and assistant).
        pairs = [
            st.session_state.chat_history[i : i + 2]
            for i in range(0, len(st.session_state.chat_history), 2)
        ]
        for pair in reversed(pairs):
            if len(pair) == 2:
                user_msg, assistant_msg = pair
                st.chat_message("user").write(user_msg["content"])
                st.chat_message("assistant").write(assistant_msg["content"])
            else:
                msg = pair[0]
                st.markdown(
                    f"<div style='background-color:#DCF8C6; padding:10px; border-radius:10px; margin-bottom:5px; text-align:left;'>"
                    f"<strong>{msg['role'].capitalize()}:</strong> {msg['content']}</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.header("Our Products")
    cols = st.columns(3)
    for idx, (product, img_path) in enumerate(product_images.items()):
        col = cols[idx % 3]
        if os.path.exists(img_path):
            col.image(img_path, width=300)
            col.markdown(
                f"<p style='font-size:20px; font-weight:bold; text-align:left;'>{product}</p>",
                unsafe_allow_html=True,
            )
        else:
            col.warning(f"Image not found: {img_path}")


if __name__ == "__main__":
    main()
