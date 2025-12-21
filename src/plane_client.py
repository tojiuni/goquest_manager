import httpx
from typing import Dict, Any, Optional, List
from src.config import get_settings


class PlaneAPIClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = f"{settings.PLANE_API_BASE_URL}/workspaces/{settings.PLANE_WORKSPACE_SLUG}"
        self.headers = {
            "Authorization": f"Bearer {settings.PLANE_API_KEY}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        with httpx.Client(follow_redirects=True) as client:
            try:
                response = client.request(
                    method, f"{self.base_url}/{endpoint}", headers=self.headers, **kwargs
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"API Error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                print(f"Request failed: {e}")
                raise

    def create_project(self, name: str) -> Dict[str, Any]:
        payload = {"name": name}
        return self._request("POST", "projects", json=payload)

    def create_cycle(
        self, project_id: str, name: str, start_date: Optional[str], end_date: Optional[str]
    ) -> Dict[str, Any]:
        payload = {"name": name, "start_date": start_date, "end_date": end_date}
        return self._request(
            "POST", f"projects/{project_id}/cycles", json=payload
        )

    def create_module(self, project_id: str, name: str) -> Dict[str, Any]:
        payload = {"name": name}
        return self._request(
            "POST", f"projects/{project_id}/modules", json=payload
        )

    def create_issue(
        self,
        project_id: str,
        name: str,
        priority: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {"name": name, "priority": priority, "parent": parent_id}
        # Filter out None values
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request(
            "POST", f"projects/{project_id}/issues", json=payload
        )

    def add_issue_to_cycle(self, project_id: str, cycle_id: str, issue_ids: List[str]) -> Dict[str, Any]:
        payload = {"issues": issue_ids}
        return self._request(
            "POST", f"projects/{project_id}/cycles/{cycle_id}/cycle-issues", json=payload
        )
    
    def add_issue_to_module(self, project_id: str, module_id: str, issue_ids: List[str]) -> Dict[str, Any]:
        payload = {"module_issues": issue_ids}
        return self._request(
            "POST", f"projects/{project_id}/modules/{module_id}/module-issues", json=payload
        )

    def delete_issue(self, project_slug: str, issue_id: str):
        return self._request("DELETE", f"projects/{project_slug}/issues/{issue_id}")

    def delete_module(self, project_slug: str, module_id: str):
        return self._request("DELETE", f"projects/{project_slug}/modules/{module_id}")

    def delete_cycle(self, project_slug: str, cycle_id: str):
        return self._request("DELETE", f"projects/{project_slug}/cycles/{cycle_id}")

    def delete_project(self, project_slug: str):
        # Note: Plane API might use ID instead of slug for deletion.
        # This is an assumption based on common practices.
        # If it uses the ID, this method will need adjustment.
        # Let's assume we need the project ID for deletion.
        # For now, this is a placeholder.
        # A get_project method would be needed to get the ID from the slug.
        # Or, we store the ID during creation. The current design does this.
        return self._request("DELETE", f"projects/{project_slug}")

