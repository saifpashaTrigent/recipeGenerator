import os
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI

# llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

azureLlm = AzureChatOpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    api_version=os.getenv("AZURE_API_VERSION"),
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_MODEL"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    temperature=0.1,
)

Azureclient = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    api_version=os.getenv("AZURE_API_VERSION"),
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_MODEL"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
)
