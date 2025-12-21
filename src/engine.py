from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from src.template_parser import parse_template
from src.plane_client import PlaneAPIClient
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

    def run_creation(self, template_path: Path):
        db: Session = next(get_db())
        template = parse_template(template_path)

        batch = SyncBatch(template_name=template.batch_name, status=SyncStatus.RUNNING)
        db.add(batch)
        db.commit()
        db.refresh(batch)

        print(f"Starting batch '{batch.id}' for template '{template.batch_name}'")

        try:
            for proj_template in template.projects:
                # For simplicity, we create a new project every time.
                # A real-world scenario might involve checking if it exists.
                project_data = self.plane_client.create_project(name=proj_template.name)
                project_id = project_data["id"]
                project_slug = project_data["identifier"] # Assuming API returns 'identifier' as slug
                
                self._save_resource(
                    db, batch.id, ResourceType.PROJECT, project_id, project_slug
                )
                print(f"  Created Project: {proj_template.name} ({project_id})")

                # Store created cycle and module IDs for issue linking
                cycle_ids = {}
                for cycle_template in proj_template.cycles:
                    cycle_data = self.plane_client.create_cycle(
                        project_id=project_id,
                        name=cycle_template.name,
                        start_date=cycle_template.start_date.isoformat() if cycle_template.start_date else None,
                        end_date=cycle_template.end_date.isoformat() if cycle_template.end_date else None,
                    )
                    cycle_id = cycle_data["id"]
                    cycle_ids[cycle_template.name] = cycle_id
                    self._save_resource(
                        db, batch.id, ResourceType.CYCLE, cycle_id, project_slug
                    )
                    print(f"    Created Cycle: {cycle_template.name} ({cycle_id})")

                module_ids = {}
                for module_template in proj_template.modules:
                    module_data = self.plane_client.create_module(
                        project_id=project_id, name=module_template.name
                    )
                    module_id = module_data["id"]
                    module_ids[module_template.name] = module_id
                    self._save_resource(
                        db, batch.id, ResourceType.MODULE, module_id, project_slug
                    )
                    print(f"    Created Module: {module_template.name} ({module_id})")

                for issue_template in proj_template.issues:
                    issue_data = self.plane_client.create_issue(
                        project_id=project_id,
                        name=issue_template.name,
                        priority=issue_template.priority,
                    )
                    issue_id = issue_data["id"]
                    self._save_resource(
                        db, batch.id, ResourceType.ISSUE, issue_id, project_slug
                    )
                    print(f"      Created Issue: {issue_template.name} ({issue_id})")

                    # Link to cycle/module
                    if issue_template.cycle and issue_template.cycle in cycle_ids:
                        self.plane_client.add_issue_to_cycle(project_id, cycle_ids[issue_template.cycle], [issue_id])
                        print(f"        - Linked to cycle '{issue_template.cycle}'")
                    
                    if issue_template.module and issue_template.module in module_ids:
                        self.plane_client.add_issue_to_module(project_id, module_ids[issue_template.module], [issue_id])
                        print(f"        - Linked to module '{issue_template.module}'")

                    # Create sub-issues
                    for sub_issue_template in issue_template.sub_issues:
                        sub_issue_data = self.plane_client.create_issue(
                            project_id=project_id,
                            name=sub_issue_template.name,
                            priority=sub_issue_template.priority,
                            parent_id=issue_id,
                        )
                        sub_issue_id = sub_issue_data["id"]
                        self._save_resource(
                            db,
                            batch.id,
                            ResourceType.ISSUE,
                            sub_issue_id,
                            project_slug,
                            parent_id=issue_id,
                        )
                        print(f"        Created Sub-issue: {sub_issue_template.name} ({sub_issue_id})")

            batch.status = SyncStatus.COMPLETED
            db.commit()
            print(f"Batch '{batch.id}' completed successfully.")

        except Exception as e:
            print(f"Error during batch execution: {e}")
            batch.status = SyncStatus.FAILED
            db.commit()
            # Here you could trigger a partial cleanup if needed
        finally:
            db.close()

    def _save_resource(
        self,
        db: Session,
        batch_id: uuid.UUID,
        resource_type: ResourceType,
        plane_id: uuid.UUID,
        project_slug: str,
        parent_id: Optional[uuid.UUID] = None,
    ):
        resource = CreatedResource(
            batch_id=batch_id,
            resource_type=resource_type,
            plane_id=plane_id,
            project_slug=project_slug,
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
                    self.plane_client.delete_issue(resource.project_slug, resource.plane_id)
                elif resource.resource_type == ResourceType.MODULE:
                    print(f"  Deleting Module: {resource.plane_id}")
                    self.plane_client.delete_module(resource.project_slug, resource.plane_id)
                elif resource.resource_type == ResourceType.CYCLE:
                    print(f"  Deleting Cycle: {resource.plane_id}")
                    self.plane_client.delete_cycle(resource.project_slug, resource.plane_id)
                elif resource.resource_type == ResourceType.PROJECT:
                    print(f"  Deleting Project: {resource.plane_id}")
                    # The client uses slug, but we stored the ID.
                    # Assuming we can delete by project ID (more robust).
                    # The current plane_client needs a delete_project_by_id method.
                    # Let's assume the current delete_project takes an ID, not slug.
                    self.plane_client.delete_project(resource.plane_id)
                
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

