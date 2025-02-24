import os
from openai import OpenAI
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

# llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

azureLlm = AzureChatOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_API_VERSION"),
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_MODEL"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    temperature=0.3,
)

Azureclient = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_API_VERSION"),
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_MODEL"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
)

imageClient = OpenAI()