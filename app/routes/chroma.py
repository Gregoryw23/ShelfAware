from fastapi import APIRouter, HTTPException, status
from app.services.chroma_service import ChromaService
from app.schemas.chroma_book import ChromaBookInfo # Corrected import path


router = APIRouter()
chroma_service = ChromaService()

@router.post("/sync-from-db", status_code=status.HTTP_200_OK)
def sync_chromadb_from_db():
    """
    Manually trigger synchronization of all books from the main database to ChromaDB.
    This ensures that the ChromaDB search index is up-to-date with the latest book records,
    handling additions, updates, and deletions.
    """
    try:
        chroma_service.sync_books() # This method will handle internal dependencies
        return {"message": "ChromaDB synchronization triggered successfully."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to synchronize ChromaDB: {str(e)}")


@router.get("/similarities")
def search_books_in_chromadb(query: str, distance_threshold: float = 0.9): # Changed default to 0.9
    """
    Search for similar books in ChromaDB based on a query and a distance_threshold.
    """
    results = chroma_service.search_books(query, distance_threshold=distance_threshold)
    if not results:
        raise HTTPException(status_code=404, detail=f"No similar books found for the query: '{query}'.")

    return {"query": query, "response": results}


@router.get("/summary")
def ai_search_books_in_chromadb(query: str, distance_threshold: float = 0.9): # Changed default to 0.9
    """
    Search for similar books in ChromaDB based on a query and return a natural language summary using Ollama.
    """
    results = chroma_service.search_books(query, distance_threshold=distance_threshold)
    if not results:
        raise HTTPException(status_code=404, detail=f"No similar books found for the query: '{query}'.")

    # Generate a natural language response using Ollama
    response = chroma_service.generate_natural_language_response(query, results)
    return {"query": query, "response": response}

@router.delete("/{book_id}")
def delete_book(book_id: str):
    """
    Delete a book's vector and metadata from ChromaDB by its ID.
    
    This endpoint also highlights a task from Activity 3: Test and improve the implementation of the delete_book method.
    """
    try:
        chroma_service.delete_book(book_id)
        return {"message": f"Book with ID '{book_id}' deleted from ChromaDB successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete book from ChromaDB: {str(e)}")
