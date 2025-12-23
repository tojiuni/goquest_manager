# Plane Batch Management Service

이 서비스는 Plane API를 활용하여 YAML 템플릿 기반으로 프로젝트, 이슈, 하위 이슈를 계층 구조로 대량 생성하고, 생성된 이력을 PostgreSQL에 저장하여 언제든 일괄 삭제(Rollback)할 수 있도록 돕는 백엔드 시스템입니다.

## 🚀 주요 기능
- **YAML 기반 대량 생성**: 복잡한 계층 구조를 한 번의 API 호출로 생성
- **상태 추적**: 생성된 모든 Plane 리소스 ID를 DB에 기록
- **안전한 일괄 삭제**: 생성 역순(LIFO)으로 리소스를 자동 삭제하여 의존성 문제 해결
- **Cycles/Modules 연동**: 이슈 생성 시 특정 사이클과 모듈에 자동 할당

## 🛠️ 설치 및 설정

### 1. 환경 변수 설정
`.env` 파일을 프로젝트 루트에 생성하고 아래 내용을 입력합니다.
```env
PLANE_API_BASE_URL=[https://app.plane.so/api/v1](https://app.plane.so/api/v1)
PLANE_API_KEY=your_plane_api_token

DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=plane_manager_db

LOG_LEVEL=info

## 
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

### 
uvicorn main:app --reload --port 8019