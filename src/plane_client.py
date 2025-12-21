import httpx
from typing import Dict, Any, Optional, List
from src.config import get_settings
from src.exceptions import PlaneAPIException


class PlaneAPIClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.PLANE_API_BASE_URL
        self.headers = {
            "x-api-key": settings.PLANE_API_KEY,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, workspace_slug: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        with httpx.Client(follow_redirects=True, verify=False) as client:
            try:
                url = f"{self.base_url}/workspaces/{workspace_slug}/{endpoint}"
                response = client.request(
                    method, url, headers=self.headers, **kwargs
                )
                response.raise_for_status()

                if response.status_code == 204:
                    return {}
                
                try:
                    return response.json()
                except ValueError:
                    raise PlaneAPIException(f"Could not decode JSON from response: {response.text}")

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                text = e.response.text
                if status == 401:
                    msg = "Authentication failed. Check your PLANE_API_KEY."
                elif status == 404:
                    msg = "Resource not found. Check your PLANE_WORKSPACE_SLUG and other identifiers."
                else:
                    msg = f"API Error: {status} - {text}"
                raise PlaneAPIException(msg, status_code=status) from e
            except httpx.RequestError as e:
                raise PlaneAPIException(f"Request failed: {e}") from e
    
    def create_project(self, workspace_slug: str, name: str, slug: Optional[str] = None) -> Optional[Dict[str, Any]]:
        payload = {"name": name}
        if slug:
            payload["identifier"] = slug
        else:
            payload["identifier"] = name.lower().replace(" ", "-")
        return self._request("POST", workspace_slug, "projects", json=payload)

    def create_cycle(
        self, workspace_slug: str, project_id: str, name: str, start_date: Optional[str], end_date: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        payload = {"name": name, "start_date": start_date, "end_date": end_date}
        return self._request(
            "POST", workspace_slug, f"projects/{project_id}/cycles", json=payload
        )

    def create_module(self, workspace_slug: str, project_id: str, name: str) -> Optional[Dict[str, Any]]:
        payload = {"name": name}
        return self._request(
            "POST", workspace_slug, f"projects/{project_id}/modules", json=payload
        )

    def create_issue(
        self,
        workspace_slug: str,
        project_id: str,
        name: str,
        priority: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        payload = {"name": name, "priority": priority, "parent": parent_id}
        # Filter out None values
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request(
            "POST", workspace_slug, f"projects/{project_id}/issues", json=payload
        )

    def add_issue_to_cycle(self, workspace_slug: str, project_id: str, cycle_id: str, issue_ids: List[str]) -> Optional[Dict[str, Any]]:
        payload = {"issues": issue_ids}
        return self._request(
            "POST", workspace_slug, f"projects/{project_id}/cycles/{cycle_id}/cycle-issues", json=payload
        )
    
    def add_issue_to_module(self, workspace_slug: str, project_id: str, module_id: str, issue_ids: List[str]) -> Optional[Dict[str, Any]]:
        payload = {"module_issues": issue_ids}
        return self._request(
            "POST", workspace_slug, f"projects/{project_id}/modules/{module_id}/module-issues", json=payload
        )

    def delete_issue(self, workspace_slug: str, project_slug: str, issue_id: str):
        return self._request("DELETE", workspace_slug, f"projects/{project_slug}/issues/{issue_id}")

    def delete_module(self, workspace_slug: str, project_slug: str, module_id: str):
        return self._request("DELETE", workspace_slug, f"projects/{project_slug}/modules/{module_id}")

    def delete_cycle(self, workspace_slug: str, project_slug: str, cycle_id: str):
        return self._request("DELETE", workspace_slug, f"projects/{project_slug}/cycles/{cycle_id}")

    def delete_project(self, workspace_slug: str, project_id: str):
        return self._request("DELETE", workspace_slug, f"projects/{project_id}")

