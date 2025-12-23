import requests
from app.core.errors import APIConnectionError
from app.database.models import PlaneMember, PlaneState

class MetadataService:
    def __init__(self, client):
        self.client = client # 1단계에서 만든 PlaneClient 활용

    def sync_members(self, db, workspace_slug: str):
        """워크스페이스 멤버 목록 동기화"""
        url = f"{self.client.base_url}/workspaces/{workspace_slug}/members/"
        response = requests.get(url, headers=self.client.headers)
        
        if response.status_code == 200:
            members = response.json().get('results', [])
            for m in members:
                user = m.get('member', {})
                obj = PlaneMember(
                    id=user.get('id'),
                    email=user.get('email'),
                    display_name=user.get('display_name')
                )
                db.merge(obj) # 존재하면 update, 없으면 insert
            db.commit()
            return len(members)
        return 0

    def sync_project_states(self, db, workspace_slug: str, project_id: str):
        """특정 프로젝트의 상태(States) 목록 동기화"""
        url = f"{self.client.base_url}/workspaces/{workspace_slug}/projects/{project_id}/states/"
        response = requests.get(url, headers=self.client.headers)
        
        if response.status_code == 200:
            states = response.json().get('results', []) # 혹은 리스트 구조 확인 필요
            for s in states:
                obj = PlaneState(
                    id=s.get('id'),
                    project_id=project_id,
                    name=s.get('name'),
                    group=s.get('group')
                )
                db.merge(obj)
            db.commit()
            return len(states)
        return 0