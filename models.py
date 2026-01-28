from sqlalchemy import Column, Integer, String, Boolean
from database import Base

# Ye database ke andar "tasks" naam ki table banayega
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    completed = Column(Boolean, default=False)
