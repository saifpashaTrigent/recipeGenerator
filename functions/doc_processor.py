import os
import time
import openai
import asyncio
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.text_splitter import RecursiveCharacterTextSplitter
from functions.prompt import system_prompt
from services.constants import DATA_FOLDER, VECTOR_DB

load_dotenv(override=True)

# Initialize embeddings
embeddings = OpenAIEmbeddings()


def get_pdf_texts():
    """
    Load all PDFs from the "docs" folder.
    """
    loader = PyPDFDirectoryLoader(DATA_FOLDER)
    documents = loader.load()
    return documents


def create_knowledge_hub(documents):
    """
    Build and save the FAISS index (knowledge base) from the provided documents.
    The index will be saved in a folder called "faiss_index".

    This function also splits the documents into manageable chunks using a text splitter.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_documents = text_splitter.split_documents(documents)
    knowledge_hub = FAISS.from_documents(split_documents, embeddings)
    knowledge_hub.save_local(VECTOR_DB)
    return knowledge_hub


def get_knowledge_hub_instance():
    """
    Loads the FAISS knowledge hub if it exists.
    If not, it creates the knowledge hub by processing the PDFs in the docs folder.
    """
    if os.path.exists(VECTOR_DB):
        return FAISS.load_local(
            VECTOR_DB, embeddings, allow_dangerous_deserialization=True
        )
    else:
        documents = get_pdf_texts()
        create_knowledge_hub(documents)
        return FAISS.load_local(
            VECTOR_DB, embeddings, allow_dangerous_deserialization=True
        )


def get_conversational_chain(tool, ques):
    """
    Set up the conversational chain with your LLM and the retrieval tool.
    """
    # llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    llm = AzureChatOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_deployment=os.getenv("AZURE_DEPLOYMENT_MODEL"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        temperature=0.1,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(llm, [tool], prompt)
    agent_executor = AgentExecutor(agent=agent, tools=[tool], verbose=True)
    response = agent_executor.invoke({"input": ques})
    return response


async def generate_recipe(user_question):
    try:
        new_db = await asyncio.to_thread(get_knowledge_hub_instance)
    except Exception as e:
        st.error("Error loading/creating the knowledge base. Please try updating it.")
        return

    retriever = new_db.as_retriever()
    retrieval_chain = create_retriever_tool(
        retriever,
        "pdf_extractor",
        "Tool to answer queries from the Canprev knowledge base PDFs.",
    )
    # Offload the blocking call to a thread:
    response = await asyncio.to_thread(get_conversational_chain, retrieval_chain, user_question)
    return response



async def generate_recipe_image(recipe_text):
    prompt = f"Generate a high-quality, appetizing image for a dish described as: {recipe_text[:200]}"
    try:
        response = openai.images.generate (prompt=prompt, n=1, size="512x512")
        return response.data[0].url
    except Exception as e:
        st.error(f"Error generating recipe image: {e}")
        return None


async def generate_product_description(product):
    """
    Query the internal knowledge base to extract a detailed description for the given product.
    This function uses the existing generate_recipe function with a specialized prompt.
    """
    # Create a prompt that instructs the system to provide a product description.
    query = (
        f"Provide a detailed product description for the Canprev product '{product}'. "
        "Include information about its benefits, key ingredients, and usage instructions, "
        "based on the internal knowledge base."
    )
    result = await generate_recipe(query)
    return result["output"]


def stream_data(content):
    for word in content.split(" "):
        yield word + " "
        time.sleep(0.02)
