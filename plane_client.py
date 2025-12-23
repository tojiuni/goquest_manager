import httpx
import os
from dotenv import load_dotenv

load_dotenv()

class PlaneClient:
    def __init__(self):
        self.base_url = os.getenv("PLANE_API_BASE_URL", "https://api.plane.so/api/v1").rstrip('/')
        self.api_key = os.getenv("PLANE_API_KEY", "plane_api_653a1683eb974cc28d752cf8c5f1c6a5")
        self.headers = {
            "x-api-key": self.api_key, 
            "Content-Type": "application/json"
        }

    async def _post(self, url, data):
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=data, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def create_project(self, workspace_slug, data):
        url = f"{self.base_url}/workspaces/{workspace_slug}/projects/"
        return await self._post(url, data)

    async def create_cycle(self, workspace_slug, project_id, data):
        url = f"{self.base_url}/workspaces/{workspace_slug}/projects/{project_id}/cycles/"
        return await self._post(url, data)

    async def link_cycle_issues(self, workspace_slug, project_id, cycle_id, issue_ids):
        url = f"{self.base_url}/workspaces/{workspace_slug}/projects/{project_id}/cycles/{cycle_id}/cycle-issues/"
        return await self._post(url, {"issues": issue_ids})

    async def create_module(self, workspace_slug, project_id, data):
        url = f"{self.base_url}/workspaces/{workspace_slug}/projects/{project_id}/modules/"
        return await self._post(url, data)

    async def link_module_issues(self, workspace_slug, project_id, module_id, issue_ids):
        url = f"{self.base_url}/workspaces/{workspace_slug}/projects/{project_id}/modules/{module_id}/module-issues/"
        return await self._post(url, {"issues": issue_ids})

    async def create_work_item(self, workspace_slug, project_id, data):
        url = f"{self.base_url}/workspaces/{workspace_slug}/projects/{project_id}/work-items/"
        return await self._post(url, data)

    async def delete_resource(self, workspace_slug, resource_type, project_id, plane_id):
        # 리소스 타입별 엔드포인트 매핑
        endpoint_map = {
            "ISSUE": f"work-items/{plane_id}/",
            "CYCLE": f"cycles/{plane_id}/",
            "MODULE": f"modules/{plane_id}/",
            "PROJECT": "" 
        }
        
        url = f"{self.base_url}/workspaces/{workspace_slug}/projects/{project_id}/{endpoint_map[resource_type]}"
        if resource_type == "PROJECT":
            url = f"{self.base_url}/workspaces/{workspace_slug}/projects/{project_id}/"
            
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=self.headers)
            return resp.status_code