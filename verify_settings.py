from src.config import get_settings

try:
    settings = get_settings()
    print("Settings loaded successfully!")
    print(f"PLANE_API_BASE_URL: {settings.PLANE_API_BASE_URL}")
    print(f"DB_HOST: {settings.DB_HOST}")
except Exception as e:
    print("Error loading settings:")
    print(e)
