from pydantic import BaseModel


class Shots(BaseModel):
    shot_id: int
    preshot_description: str

    class Config:
        orm_mode = True
