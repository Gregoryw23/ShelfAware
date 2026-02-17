from pydantic import BaseModel, ConfigDict

class BookInfo(BaseModel):
    title: str
    author: str
    description: str | None = None

class BookResponse(BookInfo):
    model_config = ConfigDict(from_attributes=True)
    id: int