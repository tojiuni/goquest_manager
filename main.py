from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import database as db
import plane_client
import yaml
import asyncio

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database
    db.init_db()
    yield

app = FastAPI(lifespan=lifespan)
plane = plane_client.PlaneClient()

def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@app.post("/batch/create")
async def create_from_template(file_path: str, dbs: Session = Depends(get_db)):
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)

    workspace_slug = config.get('workspace_slug')
    batch = db.SyncBatch(template_name=config.get('batch_name'), workspace_slug=workspace_slug)
    dbs.add(batch)
    dbs.commit()

    try:
        for p_conf in config.get('projects', []):
            # 1. Project Creation
            p_data = {
                "name": p_conf['name'],
                "identifier": p_conf['identifier'],
                "description": p_conf.get('description', '')
            }
            p_resp = await plane.create_project(workspace_slug, p_data)
            project_id = p_resp['id']
            project_identifier = p_resp['identifier']
            
            p_res = db.CreatedResource(batch_id=batch.id, resource_type="PROJECT", 
                                       plane_id=project_id, project_slug=project_identifier)
            dbs.add(p_res)
            dbs.flush()

            # 2. Cycles Creation
            cycles_map = {} # name -> id
            for c_conf in p_conf.get('cycles', []):
                c_resp = await plane.create_cycle(workspace_slug, project_id, c_conf)
                cycles_map[c_conf['name']] = c_resp['id']
                
                c_res = db.CreatedResource(batch_id=batch.id, resource_type="CYCLE", 
                                           plane_id=c_resp['id'], project_slug=project_identifier)
                dbs.add(c_res)
            dbs.flush()

            # 3. Modules Creation
            modules_map = {} # name -> id
            for m_conf in p_conf.get('modules', []):
                m_resp = await plane.create_module(workspace_slug, project_id, m_conf)
                modules_map[m_conf['name']] = m_resp['id']
                
                m_res = db.CreatedResource(batch_id=batch.id, resource_type="MODULE", 
                                           plane_id=m_resp['id'], project_slug=project_identifier)
                dbs.add(m_res)
            dbs.flush()

            # 4. Work Items (Issues) Creation
            async def create_recursive_issues(issue_list, parent_id=None):
                for i_conf in issue_list:
                    # Prepare data - include all fields from curl example if present in yaml
                    i_data = {
                        "name": i_conf['name'],
                        "description_html": i_conf.get('description_html', ''),
                        "state": i_conf.get('state', 'backlog'),
                        "priority": i_conf.get('priority', 'none'),
                        "parent": parent_id,
                        "assignees": i_conf.get('assignees', []),
                        "labels": i_conf.get('labels', []),
                        "start_date": i_conf.get('start_date'),
                        "target_date": i_conf.get('target_date'),
                        "estimate_point": i_conf.get('estimate_point'),
                        "type": i_conf.get('type')
                    }
                    
                    # Resolve module ID if name is provided
                    if 'module' in i_conf and i_conf['module'] in modules_map:
                        i_data['module'] = modules_map[i_conf['module']]
                    
                    i_resp = await plane.create_work_item(workspace_slug, project_id, i_data)
                    issue_id = i_resp['id']
                    
                    # DB Record
                    i_res = db.CreatedResource(batch_id=batch.id, resource_type="ISSUE", 
                                               plane_id=issue_id, project_slug=project_identifier)
                    dbs.add(i_res)
                    
                    # Link to cycle if specified
                    if 'cycle' in i_conf and i_conf['cycle'] in cycles_map:
                        await plane.link_cycle_issues(workspace_slug, project_id, cycles_map[i_conf['cycle']], [issue_id])
                    
                    # Recurse for sub-issues
                    if 'sub_issues' in i_conf:
                        await create_recursive_issues(i_conf['sub_issues'], parent_id=issue_id)

            await create_recursive_issues(p_conf.get('issues', []))
            dbs.flush()

        batch.status = "COMPLETED"
        dbs.commit()
        return {"status": "success", "batch_id": batch.id}

    except Exception as e:
        dbs.rollback()
        batch.status = "FAILED"
        dbs.commit()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/batch/{batch_id}")
async def delete_batch(batch_id: str, dbs: Session = Depends(get_db)):
    batch = dbs.query(db.SyncBatch).filter_by(id=batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    workspace_slug = batch.workspace_slug
    # 생성 역순(LIFO)으로 조회
    resources = dbs.query(db.CreatedResource).filter_by(batch_id=batch_id).order_by(db.CreatedResource.created_at.desc()).all()
    
    deleted_count = 0
    for res in resources:
        try:
            status = await plane.delete_resource(workspace_slug, res.resource_type, res.project_slug, res.plane_id)
            if status in [200, 204, 404]:
                dbs.delete(res)
                deleted_count += 1
        except Exception as e:
            print(f"Error deleting {res.resource_type} {res.plane_id}: {e}")
    
    batch.status = "DELETED"
    dbs.commit()
    return {"message": f"{deleted_count} resources processed (deleted or confirmed gone)."}