import os
import streamlit as st
from dotenv import load_dotenv
from functions.product_details import product_categories, product_images
from functions.recipeProcessor import (
    get_pdf_texts,
    create_knowledge_hub,
    get_knowledge_hub_instance,
    stream_data,
)
from functions.searchBarProcessor import (
    get_autocomplete_suggestions,
    update_autocomplete,
    generate_knowledge_answer,
)
from services.constants import CANPREV_IMAGE_PATH

load_dotenv(override=True)


def get_similar_products_kb(query):
    """
    Load the knowledge base, retrieve relevant documents for the query,
    then search those documents for known product names (from product_images).
    Returns a list of matching product names. If none are found, return a default list.
    """
    try:
        knowledge_db = get_knowledge_hub_instance()
    except Exception as e:
        st.error("Error loading knowledge base. Please try updating it.")
        return []

    retriever = knowledge_db.as_retriever(search_type="mmr", search_kwargs={"k": 1})
    results = retriever.get_relevant_documents(query)
    similar = set()
    # For each retrieved document, check if any known product name appears.
    for doc in results:
        text = doc.page_content
        for product in product_images.keys():
            if product.lower() in text.lower():
                similar.add(product)
    # Fallback: if no similar products found, return the first 3 products as default.
    if not similar:
        similar = set(list(product_images.keys())[:3])

    return list(similar)


def display_similar_products(similar_products):
    """
    Display similar products as image thumbnails.
    """
    if similar_products:
        st.markdown("### Similar Products")
        cols = st.columns(len(similar_products))
        for idx, prod in enumerate(similar_products):
            img_path = product_images.get(prod)
            if img_path and os.path.exists(img_path):
                cols[idx].image(img_path, width=200)
                cols[idx].caption(prod)
            else:
                cols[idx].warning(f"Image not found for {prod}")


def main():
    st.set_page_config(page_title="Product Q&A", page_icon="🍲", layout="wide")

    # Sidebar: About and Knowledge Base update.
    with st.sidebar:
        st.image(CANPREV_IMAGE_PATH, width=200)
        st.markdown("## About Canprev")
        st.markdown(
            """
            **Canprev** is a leading provider of innovative health and wellness products.  
            Our research-backed formulations help you achieve your health goals.  
            Ask any question about our products!
            """
        )
        st.markdown("---")
        if st.button("Build/Update Knowledge Base", type="primary"):
            with st.spinner("Building the knowledge base from PDF files..."):
                documents = get_pdf_texts()
                create_knowledge_hub(documents)
                st.success("Knowledge Base updated successfully!")

    # Main title and instructions.
    st.title("Product Q&A")
    st.markdown("Ask a question about our products....")

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
            if st.button(suggestion, key=suggestion, type="primary"):
                # Update effective query without modifying the widget value.
                st.session_state.effective_query = suggestion
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

    # When the user clicks "Submit".
    if st.button("Submit", type="primary"):
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
    # Display similar products only if there's at least one conversation message.
    if st.session_state.chat_history:
        query_for_similar = st.session_state.get(
            "effective_query", st.session_state.user_query
        )
        if query_for_similar:
            similar_products = get_similar_products_kb(query_for_similar)
            display_similar_products(similar_products)

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
