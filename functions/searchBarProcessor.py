import json
import streamlit as st
from services.utils import azureLlm, Azureclient
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from functions.recipeProcessor import get_knowledge_hub_instance
from langchain.tools.retriever import create_retriever_tool
from services.prompt import system_prompt_search_bar




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
        response = Azureclient.chat.completions.create(
            model="gpt-4o",  # Adjust if needed.
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that provides autocomplete suggestions for product questions, "
                        "with a special focus on Canprev's innovative health and wellness products. "
                        "Return your answer as a JSON array of strings without any additional explanation."
                    ),
                },
                {"role": "user", "content": prompt},
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


def get_conversational_chain_search_bar(tool, ques):
    """
    Set up the conversational chain with your LLM and the retrieval tool.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_search_bar),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(azureLlm, [tool], prompt)
    agent_executor = AgentExecutor(agent=agent, tools=[tool], verbose=True)
    response = agent_executor.invoke({"input": ques})
    return response


def generate_knowledge_answer(query):
    """
    Loads (or creates) the knowledge hub, creates a retrieval tool,
    and then generates an answer to the query using the conversational chain.
    """
    try:
        knowledge_db = get_knowledge_hub_instance()
    except Exception as e:
        st.error("Error loading/creating the knowledge base. Please try updating it.")
        return {"output": "Error loading knowledge base."}

    retriever = knowledge_db.as_retriever()
    retrieval_chain = create_retriever_tool(
        retriever,
        "pdf_extractor",
        "Tool to answer queries from the Canprev knowledge base PDFs.",
    )
    response = get_conversational_chain_search_bar(retrieval_chain, query)
    return response
