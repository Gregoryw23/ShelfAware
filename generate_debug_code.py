#!/usr/bin/env python3
"""Add a debug endpoint to capture the exact validation error."""

# Add this to app/routes/bookshelf.py after the imports

debug_code = '''
# DEBUG: Add a test endpoint to capture exact validation error
@router.post("/debug-add", status_code=200)
async def debug_add_book(request):
    """Debug endpoint that logs exact request body and validation details."""
    import json
    from fastapi import Request
    
    try:
        # Get raw body
        raw_body = await request.body()
        print(f"Raw request body: {raw_body}")
        
        body_text = raw_body.decode('utf-8')
        print(f"Body as text: {body_text}")
        
        body_json = json.loads(body_text)
        print(f"Body as JSON: {body_json}")
        
        # Try to validate
        from app.schemas.bookshelf import BookshelfCreate
        payload = BookshelfCreate(**body_json)
        
        return {"status": "ok", "payload": payload.model_dump()}
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
'''

print("Add this code to app/routes/bookshelf.py:")
print(debug_code)
