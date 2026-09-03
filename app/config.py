import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar .env desde backend/.env o desde el directorio actual
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, "..", ".env"))
load_dotenv(os.path.join(basedir, "..", "..", ".env"))
load_dotenv()


class Config:
    # URL de base de datos PostgreSQL: barbarito por defecto o variable de nube (Render, Neon, Supabase)
    _db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:15caconasa15@localhost:5432/barbarito",
    )
    if _db_url and _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de JWT (8 horas)
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "clave-secreta-jwt-sistema-almacen-2026-seguro"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_SECONDS", 28800))
    )

    FRONTEND_URL = os.getenv(
        "FRONTEND_URL", "http://localhost:5173,http://localhost:3000"
    )
    JSON_SORT_KEYS = False
