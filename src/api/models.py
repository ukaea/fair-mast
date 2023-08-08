from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Shots(Base):
    __tablename__ = "shots"

    shot_id = Column(Integer, primary_key=True, index=True)
    preshot_description = Column(String, unique=False, index=False)
