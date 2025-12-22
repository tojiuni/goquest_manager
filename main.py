from app.core.config import settings
from app.services.plane_client import PlaneClient
from app.database.session import SessionLocal
from app.database.models import LogTable

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

if __name__ == "__main__":
    # 테스트용 workspace_slug 입력
    run_step_1("lyckabc")