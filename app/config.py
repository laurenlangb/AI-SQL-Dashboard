"""Loads the .env variables from the environment"""
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "example.db"))
