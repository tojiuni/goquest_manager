from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
import traceback
from fastapi import HTTPException
from src.template_parser import parse_template
from src.plane_client import PlaneAPIClient
from src.exceptions import PlaneAPIException
from src.models import (
    get_db,
    SyncBatch,
    CreatedResource,
    SyncStatus,
    ResourceType,
)
import uuid


class ExecutionEngine:
    def __init__(self):
        self.plane_client = PlaneAPIClient()

    def run_creation(self, template_path: Path) -> SyncBatch:
        db: Session = next(get_db())
        template = parse_template(template_path)

        batch = SyncBatch(template_name=template.batch_name, status=SyncStatus.RUNNING)
        db.add(batch)
        db.commit()
        db.refresh(batch)

        try:
            workspace_slug = template.workspace_slug
            for proj_template in template.projects:
                project_data = self.plane_client.create_project(
                    workspace_slug=workspace_slug, name=proj_template.name, slug=proj_template.slug
                )
                if not project_data or "id" not in project_data:
                    raise Exception(f"Failed to create project '{proj_template.name}'.")
                
                project_id = project_data["id"]
                project_slug = project_data["identifier"]
                
                self._save_resource(
                    db, batch.id, ResourceType.PROJECT, project_id, project_slug, workspace_slug=workspace_slug
                )

                cycle_ids = {}
                for cycle_template in proj_template.cycles:
                    cycle_data = self.plane_client.create_cycle(
                        workspace_slug=workspace_slug,
                        project_id=project_id,
                        name=cycle_template.name,
                        start_date=cycle_template.start_date.isoformat() if cycle_template.start_date else None,
                        end_date=cycle_template.end_date.isoformat() if cycle_template.end_date else None,
                    )
                    if not cycle_data or "id" not in cycle_data:
                        continue
                    cycle_id = cycle_data["id"]
                    cycle_ids[cycle_template.name] = cycle_id
                    self._save_resource(
                        db, batch.id, ResourceType.CYCLE, cycle_id, project_slug, workspace_slug=workspace_slug
                    )

                module_ids = {}
                for module_template in proj_template.modules:
                    module_data = self.plane_client.create_module(
                        workspace_slug=workspace_slug, project_id=project_id, name=module_template.name
                    )
                    if not module_data or "id" not in module_data:
                        continue
                    module_id = module_data["id"]
                    module_ids[module_template.name] = module_id
                    self._save_resource(
                        db, batch.id, ResourceType.MODULE, module_id, project_slug, workspace_slug=workspace_slug
                    )

                for issue_template in proj_template.issues:
                    issue_data = self.plane_client.create_issue(
                        workspace_slug=workspace_slug,
                        project_id=project_id,
                        name=issue_template.name,
                        priority=issue_template.priority,
                    )
                    if not issue_data or "id" not in issue_data:
                        continue
                    issue_id = issue_data["id"]
                    self._save_resource(
                        db, batch.id, ResourceType.ISSUE, issue_id, project_slug, workspace_slug=workspace_slug
                    )

                    if issue_template.cycle and issue_template.cycle in cycle_ids:
                        self.plane_client.add_issue_to_cycle(workspace_slug, project_id, cycle_ids[issue_template.cycle], [issue_id])
                    
                    if issue_template.module and issue_template.module in module_ids:
                        self.plane_client.add_issue_to_module(workspace_slug, project_id, module_ids[issue_template.module], [issue_id])

                    for sub_issue_template in issue_template.sub_issues:
                        sub_issue_data = self.plane_client.create_issue(
                            workspace_slug=workspace_slug,
                            project_id=project_id,
                            name=sub_issue_template.name,
                            priority=sub_issue_template.priority,
                            parent_id=issue_id,
                        )
                        if not sub_issue_data or "id" not in sub_issue_data:
                            continue
                        sub_issue_id = sub_issue_data["id"]
                        self._save_resource(
                            db,
                            batch.id,
                            ResourceType.ISSUE,
                            sub_issue_id,
                            project_slug,
                            workspace_slug=workspace_slug,
                            parent_id=issue_id,
                        )

            batch.status = SyncStatus.COMPLETED
            db.commit()
            db.refresh(batch)
            return batch
        
        except PlaneAPIException as e:
            traceback.print_exc()
            batch.status = SyncStatus.FAILED
            db.commit()
            raise HTTPException(status_code=e.status_code or 500, detail=str(e))
        except Exception as e:
            traceback.print_exc()
            batch.status = SyncStatus.FAILED
            db.commit()
            raise e
        finally:
            db.close()

    def _save_resource(
        self,
        db: Session,
        batch_id: uuid.UUID,
        resource_type: ResourceType,
        plane_id: uuid.UUID,
        project_slug: str,
        workspace_slug: Optional[str] = None,
        parent_id: Optional[uuid.UUID] = None,
    ):
        resource = CreatedResource(
            batch_id=batch_id,
            resource_type=resource_type,
            plane_id=plane_id,
            project_slug=project_slug,
            workspace_slug=workspace_slug,
            parent_id=parent_id,
        )
        db.add(resource)
        db.commit()

    def run_cleanup(self, batch_id: uuid.UUID):
        db: Session = next(get_db())
        
        batch = db.query(SyncBatch).filter(SyncBatch.id == batch_id).first()
        if not batch:
            print(f"Batch with ID {batch_id} not found.")
            return

        print(f"Starting cleanup for batch '{batch.id}'")
        
        resources_to_delete = db.query(CreatedResource).filter(
            CreatedResource.batch_id == batch_id
        ).order_by(CreatedResource.created_at.desc()).all()

        for resource in resources_to_delete:
            try:
                if resource.resource_type == ResourceType.ISSUE:
                    print(f"  Deleting Issue: {resource.plane_id}")
                    self.plane_client.delete_issue(resource.workspace_slug, resource.project_slug, resource.plane_id)
                elif resource.resource_type == ResourceType.MODULE:
                    print(f"  Deleting Module: {resource.plane_id}")
                    self.plane_client.delete_module(resource.workspace_slug, resource.project_slug, resource.plane_id)
                elif resource.resource_type == ResourceType.CYCLE:
                    print(f"  Deleting Cycle: {resource.plane_id}")
                    self.plane_client.delete_cycle(resource.workspace_slug, resource.project_slug, resource.plane_id)
                elif resource.resource_type == ResourceType.PROJECT:
                    print(f"  Deleting Project: {resource.plane_id}")
                    self.plane_client.delete_project(resource.workspace_slug, resource.plane_id)
                
                db.delete(resource)
                db.commit()

            except Exception as e:
                print(f"Error deleting resource {resource.plane_id}: {e}")
                batch.status = SyncStatus.PARTIAL_DELETED
                db.commit()
                # Decide if you want to stop or continue on error
        
        # If all resources are deleted, update batch status
        remaining_resources = db.query(CreatedResource).filter(CreatedResource.batch_id == batch_id).count()
        if remaining_resources == 0:
            batch.status = SyncStatus.DELETED
            print(f"Batch '{batch.id}' cleaned up successfully.")
        
        db.commit()
        db.close()

