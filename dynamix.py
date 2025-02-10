import os
import json
import streamlit as st
from dotenv import load_dotenv
import openai
from functions.product_details import product_images
from functions.doc_processor import get_pdf_texts, create_knowledge_hub
from services.constants import CANPREV_IMAGE_PATH

load_dotenv(override=True)

def get_autocomplete_suggestions(partial_query):
    """
    Given a partial query, ask GPT-4o to suggest completions that focus on Canprev products.
    Returns a list of suggestion strings.
    Caches results in session_state to avoid repeated calls.
    """
    if not partial_query or len(partial_query) < 3:
        return []
    
    if "autocomplete_cache" not in st.session_state:
        st.session_state.autocomplete_cache = {}
        
    if partial_query in st.session_state.autocomplete_cache:
        return st.session_state.autocomplete_cache[partial_query]
    
    # Updated prompt: Focus specifically on Canprev products.
    prompt = (
        f"Given the following partial question about Canprev products: '{partial_query}', "
        "provide three complete suggestions to finish this question that specifically reference "
        "Canprev's range of health and wellness products. "
        "Return the suggestions as a JSON array of strings using double quotes for the strings, "
        "and do not include any extra text."
    )
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # Adjust if needed.
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that provides autocomplete suggestions for product questions, "
                        "with a special focus on Canprev's innovative health and wellness products. "
                        "Return your answer as a JSON array of strings without any additional explanation."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150,
        )
        suggestions_str = response.choices[0].message.content
        suggestions = json.loads(suggestions_str)
        if not isinstance(suggestions, list):
            suggestions = []
    except Exception as e:
        st.error(f"Suggestion error: {e}")
        suggestions = []
    
    st.session_state.autocomplete_cache[partial_query] = suggestions
    return suggestions

def update_autocomplete():
    """
    Callback for text input changes.
    (No additional action required here.)
    """
    pass

def query_gpt4o(user_query, chat_history):
    """
    Given the current query and conversation history, ask GPT-4o for an answer.
    """
    system_message = (
        "You are an expert on the following products: " 
        + ", ".join(list(product_images.keys()))
        + ". Answer questions about these products in a helpful and detailed manner."
    )
    messages = [{"role": "system", "content": system_message}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_query})
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"Error: {e}"
    return answer

def main():
    st.set_page_config(page_title="Product Q&A", page_icon="🍲", layout="wide")
    
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
        if st.button("Build/Update Knowledge Base"):
            with st.spinner("Building the knowledge base from PDF files..."):
                documents = get_pdf_texts()
                create_knowledge_hub(documents)
                st.success("Knowledge Base updated successfully!")
    
    st.title("Product Q&A With AI Search Bar")
    st.markdown("Ask a question about our products. As you type, autocomplete suggestions will be provided.")
    
    if "user_query" not in st.session_state:
        st.session_state.user_query = ""
    user_query = st.text_input(
        "Search:", 
        key="user_query", 
        value=st.session_state.user_query, 
        placeholder="Type your question here...", 
        on_change=update_autocomplete
    )
    
    suggestions = get_autocomplete_suggestions(user_query) if user_query and len(user_query) >= 3 else []
    if suggestions:
        st.markdown("**Suggestions:**")
        for suggestion in suggestions:
            if st.button(suggestion, key=suggestion):
                with st.spinner("thinking..."):
                    answer = query_gpt4o(suggestion, st.session_state.get("chat_history", []))
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []
                st.session_state.chat_history.append({"role": "user", "content": suggestion})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if st.button("Submit Query"):
        if user_query:
            with st.spinner("Thinking..."):
                answer = query_gpt4o(user_query, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
    
    # Display conversation as chat messages.
    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("Conversation")
        pairs = [st.session_state.chat_history[i:i+2] for i in range(0, len(st.session_state.chat_history), 2)]
        for pair in reversed(pairs):
            if len(pair) == 2:
                user_msg, assistant_msg = pair
                st.chat_message("user").write(user_msg["content"])
                st.chat_message("assistant").write(assistant_msg["content"])
            else:
                msg = pair[0]
                st.markdown(f"<div style='background-color:#DCF8C6; padding:10px; border-radius:10px; margin-bottom:5px; text-align:left;'>"
                            f"<strong>{msg['role'].capitalize()}:</strong> {msg['content']}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.header("Our Products")
    cols = st.columns(3)
    for idx, (product, img_path) in enumerate(product_images.items()):
        col = cols[idx % 3]
        if os.path.exists(img_path):
            col.image(img_path, width=300)
            col.markdown(
                f"<p style='font-size:20px; font-weight:bold; text-align:left;'>{product}</p>", 
                unsafe_allow_html=True
            )
        else:
            col.warning(f"Image not found: {img_path}")

if __name__ == "__main__":
    main()
