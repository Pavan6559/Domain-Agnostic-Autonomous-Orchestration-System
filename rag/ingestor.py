import os
import hashlib
import json
import shutil
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from .metadata import MetadataTagger
from .utils import get_logger

logger = get_logger("RAGIngestor")

class RAGIngestor:
    """Ingestion pipeline that loads PDFs, chunks them, tags with metadata, and writes to ChromaDB."""

    def __init__(self, docs_dir: str, persist_dir: str, embedding_model_name: str = "BAAI/bge-small-en"):
        self.docs_dir = os.path.abspath(docs_dir)
        self.persist_dir = os.path.abspath(persist_dir)
        self.tracker_path = os.path.join(self.persist_dir, "ingested_files.json")
        self.embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_name)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def get_document_fingerprints(self) -> Dict[str, str]:
        """Calculates stable MD5 fingerprints for all PDF files."""
        fingerprints = {}
        if not os.path.exists(self.docs_dir):
            return fingerprints
        for fname in sorted(os.listdir(self.docs_dir)):
            if fname.lower().endswith(".pdf"):
                fpath = os.path.join(self.docs_dir, fname)
                fingerprints[fname] = self.get_file_md5(fpath)
        return fingerprints

    @staticmethod
    def get_file_md5(path: str, chunk_size: int = 1024 * 1024) -> str:
        """Returns an MD5 hash without reading large PDFs into memory at once."""
        digest = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def load_and_chunk_pdf(self, filename: str) -> List[Any]:
        """Loads a single PDF and splits it into tagged chunks."""
        fpath = os.path.join(self.docs_dir, filename)
        logger.info(f"Loading and chunking PDF: {filename}")
        try:
            loader = PyPDFLoader(fpath)
            documents = loader.load()
        except Exception as e:
            logger.error(f"Failed to load PDF {filename}: {e}")
            return []

        # Split documents
        raw_chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split {filename} into {len(raw_chunks)} raw chunks.")

        # Tag chunks using metadata tagger
        tagged_chunks = []
        for chunk in raw_chunks:
            page = chunk.metadata.get("page", 0) + 1
            meta = MetadataTagger.generate_metadata(
                filename,
                page,
                chunk.page_content,
                use_llm=False
            )
            
            # Combine the tagger's metadata with any existing metadata
            chunk.metadata.update(meta)
            tagged_chunks.append(chunk)

        return tagged_chunks

    def run_ingestion(self, force_rebuild: bool = False) -> Chroma:
        """
        Runs the ingestion pipeline. Detects changes in documents, 
        deletes old database if changed, and creates a clean new database.
        """
        os.makedirs(self.persist_dir, exist_ok=True)
        current_fingerprints = self.get_document_fingerprints()

        # Check if database is valid
        db_exists = os.path.exists(self.persist_dir) and os.path.exists(self.tracker_path)
        db_valid = False
        if db_exists and not force_rebuild:
            try:
                with open(self.tracker_path, "r", encoding="utf-8") as f:
                    saved_fingerprints = json.load(f)
                if saved_fingerprints == current_fingerprints:
                    db_valid = True
            except Exception:
                db_valid = False

        if db_valid:
            logger.info("ChromaDB index matches document directory. Loading existing store...")
            vector_db = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embedding_model,
                collection_name="rules_doc_v1"
            )
            return vector_db

        logger.info("Documents updated or first run. Re-indexing vector store...")
        if os.path.exists(self.persist_dir):
            # Clean directory first
            shutil.rmtree(self.persist_dir, ignore_errors=True)
        os.makedirs(self.persist_dir, exist_ok=True)

        all_chunks = []
        for fname in current_fingerprints.keys():
            chunks = self.load_and_chunk_pdf(fname)
            all_chunks.extend(chunks)

        if not all_chunks:
            raise ValueError(f"No PDFs loaded from {self.docs_dir}. Cannot build vector DB.")

        logger.info(f"Writing {len(all_chunks)} chunks to ChromaDB...")
        vector_db = Chroma.from_documents(
            documents=all_chunks,
            embedding=self.embedding_model,
            persist_directory=self.persist_dir,
            collection_name="rules_doc_v1"
        )

        # Write tracker file
        with open(self.tracker_path, "w", encoding="utf-8") as f:
            json.dump(current_fingerprints, f, indent=4)
            
        logger.info("ChromaDB indexing complete and tracker saved.")
        return vector_db
