import streamlit as st
from openai import OpenAI
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI

# llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

azureLlm = AzureChatOpenAI(
    api_key=st.secrets.get("AZURE_OPENAI_API_KEY"),
    api_version=st.secrets.get("AZURE_API_VERSION"),
    azure_deployment=st.secrets.get("AZURE_DEPLOYMENT_MODEL"),
    azure_endpoint=st.secrets.get("AZURE_ENDPOINT"),
    temperature=0.3,
)

Azureclient = AzureOpenAI(
    api_key=st.secrets.get("AZURE_OPENAI_API_KEY"),
    api_version=st.secrets.get("AZURE_API_VERSION"),
    azure_deployment=st.secrets.get("AZURE_DEPLOYMENT_MODEL"),
    azure_endpoint=st.secrets.get("AZURE_ENDPOINT"),
)

openai_api_key = st.secrets.get("OPENAI_API_KEY")
imageClient = OpenAI(api_key=openai_api_key)
