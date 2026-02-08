from fastapi import FastAPI
from app.db.database import engine, Base

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to ShelfAware"}