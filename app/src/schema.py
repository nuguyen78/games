from pydantic import BaseModel
from uuid import UUID


class Game(BaseModel):
    name: str
    studio: str
    release_year: int
    genre: str
    description: str