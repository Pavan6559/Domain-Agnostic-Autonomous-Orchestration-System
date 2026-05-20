print("1. import os")
import os
print("2. import shutil")
import shutil
print("3. import langchain_community")
from langchain_community.document_loaders import PyPDFLoader
print("4. import langchain_text_splitters")
from langchain_text_splitters import RecursiveCharacterTextSplitter
print("5. import langchain_huggingface")
from langchain_huggingface import HuggingFaceEmbeddings
print("6. import langchain_ollama")
from langchain_ollama import OllamaLLM
print("7. import chromadb")
from langchain_community.vectorstores import Chroma
print("All imports SUCCESSFUL")
