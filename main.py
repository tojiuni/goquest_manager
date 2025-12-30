import yaml
import os
from app.core.config import settings
from app.services.plane_client import PlaneClient
from app.database.session import SessionLocal
from app.database.models import LogTable
from app.services.metadata_service import MetadataService
from app.services.execution_engine import ExecutionEngine

def run_step_1(workspace_slug: str):
    db = SessionLocal()
    client = PlaneClient(settings.PLANE_API_BASE_URL, settings.PLANE_API_KEY)
    
    print(f"--- 1단계: 연결 테스트 시작 (Workspace: {workspace_slug}) ---")
    
    try:
        # 1. DB 연결 테스트 (Log 기록)
        db_log = LogTable(level="INFO", step="DB_CONNECT", message="Database connection check")
        db.add(db_log)
        db.commit()
        print("✅ DB 연결 및 로그 기록 성공")

        # 2. Plane API 연결 테스트
        workspace_data = client.test_connection(workspace_slug)
        print(f"✅ Plane API 연결 성공: {workspace_data.get('name')}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        db.close()
def run_step_2(workspace_slug: str, test_project_id: str = None):
    db = SessionLocal()
    client = PlaneClient(settings.PLANE_API_BASE_URL, settings.PLANE_API_KEY)
    meta_service = MetadataService(client)
    
    print(f"--- 2단계: 메타데이터 동기화 시작 ---")
    
    try:
        # 1. 멤버 동기화
        member_count = meta_service.sync_members(db, workspace_slug)
        print(f"✅ 멤버 {member_count}명 동기화 완료")

        # 2. 상태 동기화 (기존 프로젝트 ID가 있는 경우)
        if test_project_id:
            state_count = meta_service.sync_project_states(db, workspace_slug, test_project_id)
            print(f"✅ 프로젝트({test_project_id}) 상태 {state_count}개 동기화 완료")
            
    except Exception as e:
        print(f"❌ 2단계 오류: {e}")
    finally:
        db.close()
def run_step_3(workspace_slug: str):
    db = SessionLocal()
    client = PlaneClient(settings.PLANE_API_BASE_URL, settings.PLANE_API_KEY)
    meta_service = MetadataService(client)
    
    print(f"--- 3단계: 프로젝트 목록 동기화 시작 ---")
    
    try:
        project_count = meta_service.sync_project_list(db, workspace_slug)
        print(f"✅ 프로젝트 {project_count}개 동기화 완료")
    except Exception as e:
        print(f"❌ 3단계 오류: {e}")
    finally:
        db.close()
def run_step_4(workspace_slug: str, project_name: str, identifier: str = None):
    db = SessionLocal()
    client = PlaneClient(settings.PLANE_API_BASE_URL, settings.PLANE_API_KEY)
    meta_service = MetadataService(client)
    
    print(f"--- 4단계: 프로젝트 생성 시작 ---")
    
    try:
        project_id = meta_service.create_project(db, workspace_slug, project_name, identifier=identifier)
        print(f"✅ 프로젝트({project_id}) 생성 완료")
    except Exception as e:
        print(f"❌ 4단계 오류: {e}")
    finally:
        db.close()
def run_step_5(workspace_slug: str, project_id: str, workitem_name: str, state_id: str = None):
    db = SessionLocal()
    client = PlaneClient(settings.PLANE_API_BASE_URL, settings.PLANE_API_KEY)
    meta_service = MetadataService(client)
    
    print(f"--- 5단계: 워크아이템 생성 시작 ---")
    try:
        item_id = meta_service.create_workitem(db, workspace_slug, project_id=project_id, title=workitem_name, state_id=None)
        print(f"✅ 워크아이템({item_id}) 생성 완료")
    except Exception as e:
        print(f"❌ 5단계 오류: {e}")
    finally:
        db.close()

def run_step_6(workspace_slug: str, project_id: str, cycle_name: str, 
               start_date: str = None, end_date: str = None, description: str = None, owned_by: str = None):
    """Cycle 생성 테스트"""
    db = SessionLocal()
    client = PlaneClient(settings.PLANE_API_BASE_URL, settings.PLANE_API_KEY)
    meta_service = MetadataService(client)
    
    print(f"--- 6단계: Cycle 생성 테스트 시작 ---")
    try:
        cycle_id = meta_service.create_cycle(
            db, workspace_slug, project_id, cycle_name,
            start_date=start_date, end_date=end_date, description=description, owned_by=owned_by
        )
        if cycle_id:
            print(f"✅ Cycle({cycle_id}) 생성 완료")
        else:
            print(f"❌ Cycle 생성 실패")
    except Exception as e:
        print(f"❌ 6단계 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def run_yaml_batch(yaml_path: str = "data/batch.yaml"):
    """YAML 파일을 읽어서 ExecutionEngine으로 실행"""
    db = SessionLocal()
    client = PlaneClient(settings.PLANE_API_BASE_URL, settings.PLANE_API_KEY)
    engine = ExecutionEngine(client, db)
    
    print(f"--- YAML 배치 실행 시작: {yaml_path} ---")
    
    try:
        # YAML 파일 읽기
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"YAML 파일을 찾을 수 없습니다: {yaml_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        print(f"✅ YAML 파일 로드 완료: {yaml_data.get('batch_name')}")
        
        # ExecutionEngine 실행
        engine.execute_yaml(yaml_data)
        print("✅ 배치 실행 완료")
        
    except Exception as e:
        print(f"❌ 배치 실행 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # YAML 배치 실행
    # run_yaml_batch("data/batch.yaml")
    
    # Cycle 생성 테스트
    WS_SLUG = "gopedia"
    PROJECT_ID = "d0e3ab80-1e0c-4432-8bfd-9bf27589f7a8"  # 테스트용 프로젝트 ID
    # run_step_6(WS_SLUG, PROJECT_ID, "Test Cycle", owned_by="45c205c7-05fe-420c-b323-f2b1c54adbbf",
    #            start_date="2025-12-29", end_date="2025-12-31",
    #            description="Test Cycle Description")
    
    # 기존 단계별 실행 함수들 (주석 처리됨)
    # WS_SLUG = "lyckabc"
    # PJ_SLUG = "f5badd3d-79d9-4571-aed2-155cb03e4d66"
    # run_step_1(WS_SLUG)
    # run_step_2(WS_SLUG, PJ_SLUG)
    # run_step_3(WS_SLUG)
    # run_step_4(WS_SLUG, "test_projectB", "TestB")
    # run_step_5(WS_SLUG, "fbcb63ce-c564-40cb-819a-62c186e89577", "Test Workitem from Script", None)
    run_yaml_batch("data/batch.yaml")