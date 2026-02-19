import os # Added import for os
from fastapi import APIRouter, HTTPException, status
from app.services.chroma_service import ChromaService
from app.schemas.chroma_book import ChromaBookInfo # Corrected import path
from typing import Optional, Literal # Added Literal for llm_provider type hinting


router = APIRouter()

# Determine default LLM provider based on environment variables
# If LLM_PROVIDER is not set, it defaults to OPENAI.
# If OPENAI is the default and OPENAI_API_KEY is not set, switch to OLLAMA.
default_llm_provider_env = os.getenv("LLM_PROVIDER", "OPENAI").upper()
llm_provider_for_instance = None
if default_llm_provider_env == "OPENAI" and not os.getenv("OPENAI_API_KEY"):
    llm_provider_for_instance = "OLLAMA"
elif default_llm_provider_env == "OLLAMA":
    llm_provider_for_instance = "OLLAMA"
# If default_llm_provider_env is OPENAI and OPENAI_API_KEY is set, or if another provider is specified
# then llm_provider_for_instance will remain None and ChromaService will determine
# the provider using its internal logic (which respects LLM_PROVIDER env var).

_chroma_service_instance = ChromaService(llm_provider_override=llm_provider_for_instance)

@router.post("/sync-from-db", status_code=status.HTTP_200_OK)
def sync_chromadb_from_db(llm_provider: Optional[Literal["OPENAI", "OLLAMA"]] = None):
    """
    Manually trigger synchronization of all books from the main database to ChromaDB.
    This ensures that the ChromaDB search index is up-to-date with the latest book records,
    handling additions, updates, and deletions.
    An optional `llm_provider` can be specified to override the default for this sync operation.
    """
    try:
        # Create a new ChromaService instance to respect the llm_provider_override
        # If llm_provider is not provided, use the pre-initialized _chroma_service_instance
        if llm_provider:
            current_chroma_service = ChromaService(llm_provider_override=llm_provider)
        else:
            current_chroma_service = _chroma_service_instance

        sync_results = current_chroma_service.sync_books() # Capture the results
        upserted = sync_results.get("upserted", 0)
        deleted = sync_results.get("deleted", 0)
        return {"message": f"ChromaDB synchronization completed using {current_chroma_service.llm_provider}. Upserted: {upserted} books, Deleted: {deleted} books."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to synchronize ChromaDB: {str(e)}")


@router.get("/similarities")
def search_books_in_chromadb(query: str, distance_threshold: float = 0.9, llm_provider: Optional[Literal["OPENAI", "OLLAMA"]] = None):
    """
    Search for similar books in ChromaDB based on a query and a distance_threshold.
    An optional `llm_provider` can be specified to override the default for this search operation.
    """
    if llm_provider:
        current_chroma_service = ChromaService(llm_provider_override=llm_provider)
    else:
        current_chroma_service = _chroma_service_instance
    
    results = current_chroma_service.search_books(query, distance_threshold=distance_threshold)
    if not results:
        raise HTTPException(status_code=404, detail=f"No similar books found for the query: '{query}'.")

    return {"query": query, "response": results}


@router.get("/summary")
def ai_search_books_in_chromadb(query: str, distance_threshold: float = 0.9, llm_provider: Optional[Literal["OPENAI", "OLLAMA"]] = None):
    """
    Search for similar books in ChromaDB based on a query and return a natural language summary.
    An optional `llm_provider` can be specified to override the default for this summary generation.
    """
    if llm_provider:
        current_chroma_service = ChromaService(llm_provider_override=llm_provider)
    else:
        current_chroma_service = _chroma_service_instance

    results = current_chroma_service.search_books(query, distance_threshold=distance_threshold)
    if not results:
        raise HTTPException(status_code=404, detail=f"No similar books found for the query: '{query}'.")

    # Generate a natural language response using the selected LLM provider
    response = current_chroma_service.generate_natural_language_response(query, results)
    return {"query": query, "response": response}

@router.delete("/{book_id}")
def delete_book(book_id: str):
    """
    Delete a book's vector and metadata from ChromaDB by its ID.
    
    This endpoint also highlights a task from Activity 3: Test and improve the implementation of the delete_book method.
    """
    try:
        _chroma_service_instance.delete_book(book_id)
        return {"message": f"Book with ID '{book_id}' deleted from ChromaDB successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete book from ChromaDB: {str(e)}")
