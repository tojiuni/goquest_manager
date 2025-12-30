# app/services/plane_client.py
import requests
from app.core.errors import APIConnectionError

class PlaneClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"x-api-key": api_key}

    def test_connection(self, workspace_slug: str):
        """Workspace 정보를 조회하여 연결 확인"""
        url = f"{self.base_url}/workspaces/{workspace_slug}/projects/"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise APIConnectionError(f"Plane 연결 실패: {str(e)}", {"slug": workspace_slug})

    def post(self, url: str, payload: dict, headers: dict = None):
        """POST 요청을 보내고 응답을 반환"""
        try:
            # headers가 제공되면 사용하고, 없으면 기본 headers 사용
            request_headers = headers if headers else self.headers
            response = requests.post(url, headers=request_headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise APIConnectionError(f"Plane POST 요청 실패: {str(e)}", {"url": url, "payload": payload})