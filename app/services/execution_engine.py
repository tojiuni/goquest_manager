import uuid
from app.database.models import SyncBatch, CreatedResource, BatchStatus, PlaneState, PlaneProject

class ExecutionEngine:
    def __init__(self, client, db):
        self.client = client
        self.db = db

    def execute_yaml(self, yaml_data: dict):
        workspace_slug = yaml_data.get("Workspace Slug")
        batch_id = str(uuid.uuid4())
        
        # 1. Batch 시작 기록
        batch = SyncBatch(id=batch_id, template_name=yaml_data.get("batch_name"))
        self.db.add(batch)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"❌ Batch 생성 실패: {e}")
            raise

        try:
            for p_data in yaml_data.get("projects", []):
                # 2. Project 생성
                project_id = self._query_project_by_slug(workspace_slug, p_data["slug"])
                if not project_id:
                    project = self._create_project(workspace_slug, p_data, batch_id)
                    project_id = project['id']
                
                # 3. 해당 프로젝트의 기본 State 확보 (예: Todo)
                default_state = self.db.query(PlaneState).filter_by(project_id=project_id).first()
                state_id = default_state.id if default_state else None

                # 4. Cycles & Modules 생성 (매핑 정보 저장)
                cycle_map = self._create_cycles(workspace_slug, project_id, p_data.get("cycles", []), batch_id, p_data["slug"])
                module_map = self._create_modules(workspace_slug, project_id, p_data.get("modules", []), batch_id, p_data["slug"])

                # 5. Issues (with Hierarchy)
                self._create_issues(
                    workspace_slug, project_id, p_data.get("issues", []), 
                    batch_id, state_id, cycle_map, module_map
                )

            batch.status = BatchStatus.COMPLETED
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            batch.status = BatchStatus.FAILED
            # Batch 상태 업데이트를 위해 다시 조회
            try:
                self.db.merge(batch)
                self.db.commit()
            except:
                self.db.rollback()
            print(f"Execution Error: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _create_project(self, workspace_slug, data, batch_id):
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.client.api_key
        }
        payload = {
            "name": data["name"],
            "identifier": data["slug"],
            "module_view": True,
            "cycle_view": True,
            "issue_views_view": True,
            "page_view": True,
            "inbox_view": True
        }
        url = f"{self.client.base_url}/workspaces/{workspace_slug}/projects/"
        res = self.client.post(url, payload, headers=headers)
        
        # 생성된 프로젝트를 DB에 저장
        project = PlaneProject(
            id=res.get('id'),
            name=res.get('name'),
            slug=res.get('slug') or data["slug"]
        )
        self.db.merge(project)
        self.db.flush()
        
        self._record_resource(batch_id, "PROJECT", res['id'], data["slug"])
        return res

    def _create_issues(self, ws_slug, proj_id, issues_data, batch_id, state_id, cycle_map, module_map, parent_id=None):
        for i_data in issues_data:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.client.api_key
            }
            payload = {
                "name": i_data["name"],
                "state": state_id,
                "priority": i_data.get("priority", "none"),
                "parent": parent_id
            }
            # Cycle/Module 매핑 (이름 기반 ID 매칭)
            if "cycle" in i_data: payload["cycle"] = cycle_map.get(i_data["cycle"])
            if "module" in i_data: payload["module"] = module_map.get(i_data["module"])

            url = f"{self.client.base_url}/workspaces/{ws_slug}/projects/{proj_id}/work-items/"
            res = self.client.post(url, payload, headers=headers)
            
            # 프로젝트 slug를 얻기 위해 프로젝트 정보 조회
            project = self.db.query(PlaneProject).filter_by(id=proj_id).first()
            project_slug = project.slug if project else proj_id
            self._record_resource(batch_id, "ISSUE", res['id'], project_slug, parent_id)

            # 하위 이슈 재귀 생성
            if "sub_issues" in i_data:
                self._create_issues(ws_slug, proj_id, i_data["sub_issues"], batch_id, state_id, cycle_map, module_map, res['id'])

    def _record_resource(self, batch_id, r_type, plane_id, slug, parent_id=None):
        resource = CreatedResource(
            batch_id=batch_id,
            resource_type=r_type,
            plane_id=plane_id,
            project_slug=slug,
            parent_id=parent_id
        )
        self.db.add(resource)
        self.db.flush() # ID 확정 위해 flush

    def _query_project_by_slug(self, workspace_slug: str, project_slug: str):
        try:
            project = self.db.query(PlaneProject).filter_by(slug=project_slug).first()
            return project.id if project else None
        except Exception as e:
            # 에러 발생 시 None 반환 (프로젝트가 없거나 쿼리 실패)
            print(f"⚠️ 프로젝트 조회 중 오류 (slug: {project_slug}): {e}")
            return None

    def _create_cycles(self, workspace_slug: str, project_id: str, cycles_data: list, batch_id: str, project_slug: str):
        """Cycles를 생성하고 이름->ID 매핑 반환"""
        cycle_map = {}
        for cycle_data in cycles_data:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.client.api_key
            }
            payload = {
                "name": cycle_data["name"],
                "owned_by": "45c205c7-05fe-420c-b323-f2b1c54adbbf",
                "project_id": project_id
            }
            # 선택적 필드 추가
            if cycle_data.get("start_date"):
                payload["start_date"] = cycle_data.get("start_date")
            if cycle_data.get("end_date"):
                payload["end_date"] = cycle_data.get("end_date")
            if cycle_data.get("description"):
                payload["description"] = cycle_data.get("description")
            
            url = f"{self.client.base_url}/workspaces/{workspace_slug}/projects/{project_id}/cycles/"
            res = self.client.post(url, payload, headers=headers)
            
            cycle_id = res.get('id')
            cycle_name = cycle_data["name"]
            cycle_map[cycle_name] = cycle_id
            
            self._record_resource(batch_id, "CYCLE", cycle_id, project_slug)
        return cycle_map

    def _create_modules(self, workspace_slug: str, project_id: str, modules_data: list, batch_id: str, project_slug: str):
        """Modules를 생성하고 이름->ID 매핑 반환"""
        module_map = {}
        for module_data in modules_data:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.client.api_key
            }
            payload = {
                "name": module_data["name"]
            }
            url = f"{self.client.base_url}/workspaces/{workspace_slug}/projects/{project_id}/modules/"
            res = self.client.post(url, payload, headers=headers)
            
            module_id = res.get('id')
            module_name = module_data["name"]
            module_map[module_name] = module_id
            
            self._record_resource(batch_id, "MODULE", module_id, project_slug)
        return module_map