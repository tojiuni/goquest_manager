# app/services/plane_client.py
import requests
from app.core.errors import APIConnectionError

class PlaneClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {"x-api-key": api_key}

    def test_connection(self, workspace_slug: str):
        """Workspace 정보를 조회하여 연결 확인"""
        url = f"{self.base_url}/workspaces/{workspace_slug}/"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise APIConnectionError(f"Plane 연결 실패: {str(e)}", {"slug": workspace_slug})