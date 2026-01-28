from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Database file ka naam aur rasta
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"

# 2. Database engine banana
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Database se baat karne ke liye session setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class jisse hum Tables banayenge
Base = declarative_base()
