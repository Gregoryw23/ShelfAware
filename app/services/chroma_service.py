import chromadb
from chromadb.utils import embedding_functions # Keep this for OllamaEmbeddingFunction
from typing import List, Optional # Added Optional for consistency with ShelfAware Book model
import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.models.book import Book
from app.services.book_service import BookService

# NEW IMPORT for Ollama client
from ollama import Client as OllamaClient

load_dotenv()

class ChromaService:
    def __init__(self):
        # Initialize ChromaDB Persistent Client
        self.client = chromadb.PersistentClient(path="./chromadb")

        # --- Ollama Local Setup for Embeddings ---
        # Ensure Ollama server is running locally (default: http://localhost:11434)
        # Ensure 'embeddinggemma' model is pulled via `ollama pull embeddinggemma`
        self.embedding_function = embedding_functions.OllamaEmbeddingFunction(
            model_name="embeddinggemma", # Use the embedding model you pulled
            url="http://localhost:11434" # Default local Ollama server address
        )

        # self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
        #     api_key=os.getenv("OPENAI_API_KEY"),  # Load API key from environment
        #     model_name="text-embedding-3-small"
        # )

        # Initialize or create the "books" collection with the Ollama embedding function
        self.collection = self.client.get_or_create_collection(
            name="books",
            embedding_function=self.embedding_function
        )

        # --- Initialize Ollama Client for Natural Language Generation ---
        # Ensure Ollama server is running locally
        # Use an environment variable to select the LLM model (e.g., OLLAMA_LLM_MODEL="gemma3:270m")
        # Defaults to "gemma3:1b" if the environment variable is not set.
        self.ollama_generator_client = OllamaClient(host="http://localhost:11434")
        self.ollama_llm_for_generation = os.getenv("OLLAMA_LLM_MODEL", "gemma3:1b")
        # Ensure the chosen model is pulled via `ollama pull <model_name>`


    def add_book(self, book_id: str, title: str, abstract: Optional[str]): # Changed to abstract
        """
        Add a book's embedding to the collection.
        """
        # Adapted to handle Optional[str] for abstract
        document_content = f"{title}. {abstract}" if abstract else title
        self.collection.upsert(
            ids=[book_id],
            documents=[document_content],
            metadatas=[{"title": title, "description": abstract or ""}] # Use 'description' key for ChromaDB metadata
        )

    def search_books(self, query: str, n_results: int = 3, distance_threshold: float = 0.9) -> List[dict]:
        """
        Search for similar books based on a query with a similarity threshold.

        :param query: Query text for semantic search.
        :param n_results: Maximum number of results to retrieve.
        :param distance_threshold: Maximum similarity score to include a result.
        :return: List of metadata dictionaries for matching books.
        """
        results = self.collection.query(
            query_texts=[query], # Single query
            n_results=n_results
        )
        print(f"Raw ChromaDB query results: {results}")

        # Flatten ids, distances and metadata (results are lists of lists)
        ids = results["ids"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        # Combine id, metadata and distances for filtering
        filtered_results = [
            {"id": book_id, **metadata, "distance": distance} # Add id and distance to each metadata entry
            for book_id, metadata, distance in zip(ids, metadatas, distances)
            if distance <= distance_threshold # Filter based on distance threshold
        ]

        return filtered_results


    def generate_natural_language_response(self, query: str, search_results: List[dict]) -> str:
        """
        Use a small Ollama model to generate a concise natural language summary of the search results.
        """
        if not search_results:
            return f"No similar books found for the query: '{query}'."

        # prompt = (
        #     f"Based on the query '{query}', summarize the following books. "
        #     f"Include the number of books found and a brief description of each:\n\n"
        #     f"{search_results}\n\n"
        #     "Provide a concise summary, ideally under 100 words, focusing on relevance to the query."
        # )

        try:
            # Call Ollama API for generation
            response = self.ollama_generator_client.chat(
                model=self.ollama_llm_for_generation,
                messages=[
                    {"role": "system", "content": "You are an expert librarian assistant. Your task is to provide concise and helpful summaries of book search results based on a user's query."},
                    {"role": "user", "content": f"The user queried: '{query}'. Below is a list of search results, where each item is a dictionary containing book information. "
                                                 f"Each dictionary has 'title' and 'description' keys. "
                                                 f"Your task is to summarize these {len(search_results)} books. "
                                                 f"For each book, identify its title and provide a brief, relevant summary of its description, highlighting aspects that directly relate to the user's query. "
                                                 f"Present the summary in a clear, easy-to-read natural language format, not as a list of dictionaries. The overall summary should be concise, ideally under 100 words. \n\n"
                                                 f"Search Results (Python list of dictionaries):\n{search_results}\n\n"
                                                 f"Please provide your concise summary now."}
                ],
                options={
                    "temperature": 0.1, # Low temperature for more deterministic summaries
                    "num_predict": 200, # Max tokens for the response
                    # Add other Ollama-specific options if needed, e.g., "top_k", "top_p"
                }
            )
            return response['message']['content']
        except Exception as e:
            print(f"Error generating summary with local Ollama: {e}")
            return f"Error generating summary with local Ollama: {str(e)}. Please ensure Ollama is running and the model '{self.ollama_llm_for_generation}' is pulled."

    def delete_book(self, book_id: str):
        """
        Remove a book from the ChromaDB collection.
        """
        self.collection.delete(ids=[book_id])

    def sync_books(self):
        """
        Synchronizes books from the main database to ChromaDB.
        Handles additions, updates, and deletions to ensure ChromaDB
        reflects the current state of the main database.
        """
        db = next(get_db()) # Get a DB session
        book_service = BookService(db) # Instantiate BookService with the session

        try:
            # 1. Get all books from the main database
            db_books = book_service.get_books() # Using existing get_books method
            db_book_ids = {str(book.book_id) for book in db_books}

            # 2. Get all existing book IDs from ChromaDB
            chroma_collection_content = self.collection.get()
            chroma_book_ids = set(chroma_collection_content.get('ids', []))

            # 3. Add/Update books in ChromaDB (upsert)
            for book in db_books:
                self.add_book(str(book.book_id), book.title, book.abstract)

            # 4. Identify and delete books from ChromaDB that are no longer in the main DB
            books_to_delete_from_chroma = chroma_book_ids - db_book_ids
            if books_to_delete_from_chroma:
                self.collection.delete(ids=list(books_to_delete_from_chroma))

            # print(f"ChromaDB Sync: Upserted {len(db_books)} books. Deleted {len(books_to_delete_from_chroma)} books.")

        finally:
            db.close() # Always close the session