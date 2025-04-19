from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()

DATABASE_URL = "postgresql://imran:Yz4sq2segPLjGZ9UjdIUf6SSjIIZ9JT8@dpg-d00j5jali9vc739vkq7g-a.oregon-postgres.render.com/randtalkdb"

# Create the database engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Define a User table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    account_status = Column(String, nullable=False, default="incomplete")
    preferences = Column(String, nullable=True)  # JSON string to store user preferences
    age = Column(Integer, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    points = Column(Integer, nullable=True, default=0)
    status = Column(String, nullable=True)
    birthdate = Column(String, nullable=True)

# Define a Chat table
class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Foreign key to users table
    partner_id = Column(Integer, nullable=True)  # Foreign key to users table
    status = Column(String, nullable=False, default="waiting")  # waiting, matched, active, ended
    preferences = Column(String, nullable=True)  # Matching preferences (e.g., f/25-30/any)
    created_at = Column(String, nullable=False)  # Timestamp when the chat record was created
    updated_at = Column(String, nullable=True)  # Timestamp when the chat record was last updated

# Define a function to create tables
def create_tables():
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully, including the 'users' table.")

def get_db():
    """
    Dependency to get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Call the function to create tables
if __name__ == "__main__":
    create_tables()
