
import os
from dotenv import load_dotenv

# Load environment variables from the project-root .env file
load_dotenv()


# Application configuration
JWT_SECRET = os.getenv("JWT_SECRET", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv(
    "NVIDIA_BASE_URL",
    "https://integrate.api.nvidia.com/v1",
)
NVIDIA_MODEL = os.getenv(
    "NVIDIA_MODEL",
    "openai/gpt-oss-20b",
)
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


# Keep compatibility with code that imports settings
class Settings:
    def __init__(self):
        self.JWT_SECRET = JWT_SECRET
        self.NVIDIA_API_KEY = NVIDIA_API_KEY
        self.NVIDIA_BASE_URL = NVIDIA_BASE_URL
        self.NVIDIA_MODEL = NVIDIA_MODEL
        self.EMBEDDING_MODEL = EMBEDDING_MODEL


settings = Settings()


def validate_config():
    """Validate required application configuration."""
    missing = []

    if not JWT_SECRET:
        missing.append("JWT_SECRET")

    if not NVIDIA_API_KEY:
        missing.append("NVIDIA_API_KEY")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )
