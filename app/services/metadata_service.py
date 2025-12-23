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
            data = response.json()
            # API가 { "results": [...] } 형태거나 [...] 리스트 형태일 수 있음
            members = data.get('results', []) if isinstance(data, dict) else data
            
            for m in members:
                # API 응답 구조에 따라 'member' 키 안에 데이터가 있을 수도, 직접 있을 수도 있음
                user = m.get('member', m) if isinstance(m, dict) else {}
                if not user.get('id'):
                    continue
                    
                obj = PlaneMember(
                    id=user.get('id'),
                    email=user.get('email'),
                    display_name=user.get('display_name')
                )
                db.merge(obj)
            db.commit()
            return len(members)
        return 0

    def sync_project_states(self, db, workspace_slug: str, project_id: str):
        """특정 프로젝트의 상태(States) 목록 동기화"""
        url = f"{self.client.base_url}/workspaces/{workspace_slug}/projects/{project_id}/states/"
        response = requests.get(url, headers=self.client.headers)
        
        if response.status_code == 200:
            data = response.json()
            states = data.get('results', []) if isinstance(data, dict) else data
            
            for s in states:
                if not isinstance(s, dict) or not s.get('id'):
                    continue
                    
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