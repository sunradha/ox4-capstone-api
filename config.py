from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    ALLOWED_ORIGINS = [
        "https://future-proof-workforce-insights.lovable.app",
        "http://localhost:3000",
        "http://localhost:8080"
    ]


settings = Settings()
