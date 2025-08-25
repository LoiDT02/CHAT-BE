import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ALLOW_ORIGINS: list = ["*"]
    DEBUG: bool = False

    # SQLAlchemy config
    SQLALCHEMY_DEBUG: bool = False

    # OPA config
    OPA_SERVER: str = "http://localhost"
    OPA_SERVER_PORT: str = "8181"

    # Authentication
    JWT_SECRET: str = "changeme"

    # DB config
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "appdb"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    PGDATA: str = "/var/lib/postgresql/data"

    # OBJECT_STORAGE
    OBJECT_STORAGE_BUCKET_NAME: str = "my-bucket"
    OBJECT_STORAGE_ACCESS_KEY_ID: str = "minioadmin"
    OBJECT_STORAGE_SECRET_ACCESS_KEY: str = "minioadmin"
    OBJECT_STORAGE_REGION: str = "us-east-1"
    OBJECT_STORAGE_UPLOAD_FOLDER: str = "uploads"
    OBJECT_STORAGE_UPLOAD_EXTERNAL_FOLDER: str = "external"
    OBJECT_STORAGE_UPLOAD_ATTACHMENT_FOLDER: str = "attachments"
    OBJECT_STORAGE_ENDPOINT: str = "http://localhost:9000"

    # NOSQL
    MONGO_INITDB_ROOT_USERNAME: str = "root"
    MONGO_INITDB_ROOT_PASSWORD: str = "example"
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    JWT_SECRET: str
    tz: str = "Asia/Ho_Chi_Minh"


env_file = os.getenv("ENV_FILE", ".env.dev")
settings = Settings(_env_file=env_file, _env_file_encoding="utf-8")