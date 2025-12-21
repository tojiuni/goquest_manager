import tempfile
from pathlib import Path
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from src.engine import ExecutionEngine
from src.models import init_db, test_db_connection

app = FastAPI(
    title="GoQuest Manager",
    description="A service to manage bulk operations for GoQuest resources, powered by Plane.",
    version="0.1.0",
)

@app.on_event("startup")
def on_startup():
    # You can add logic here to run on application startup
    # For example, checking database connection
    print("Connecting to the database...")
    test_db_connection()
    # Note: It's generally better to run database migrations/initializations
    # as a separate one-time command rather than on every startup.
    # The old 'initdb' command can still be used for that.
    print("Startup complete.")


@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint to check if the service is running.
    """
    return {"status": "ok", "message": "Welcome to GoQuest Manager!"}


@app.post("/create/", tags=["Operations"])
def create_resources_from_yaml(file: UploadFile = File(..., description="YAML template file for resource creation.")):
    """
    Create Plane resources by uploading a YAML template file.

    This endpoint processes a YAML file to bulk-create projects, cycles, modules,
    and issues in a Plane workspace.
    """
    if not file.filename.endswith((".yaml", ".yml")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a YAML file.")

    engine = ExecutionEngine()

    # Use a temporary file to store the upload
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="wb") as tmp:
            tmp.write(file.file.read())
            template_path = Path(tmp.name)

        # The engine will return the batch object
        batch_info = engine.run_creation(template_path)

    except Exception as e:
        # Clean up the temp file in case of an error during processing
        if 'template_path' in locals() and template_path.exists():
            template_path.unlink()
        raise HTTPException(status_code=500, detail=f"An error occurred during resource creation: {e}")
    finally:
        # Ensure the temporary file is cleaned up after processing
        if 'template_path' in locals() and template_path.exists():
            template_path.unlink()

    if not batch_info:
        raise HTTPException(status_code=500, detail="Resource creation failed and did not return batch information.")

    return {
        "message": "Resource creation process started successfully.",
        "batch_id": batch_info.id,
        "template_name": batch_info.template_name,
        "status": batch_info.status.value,
    }

# To run this application:
# 1. Make sure you have installed the dependencies from requirements.txt:
#    pip install -r requirements.txt
# 2. Run the server with uvicorn:
#    uvicorn main:app --reload
#
# You can then access the interactive API documentation at http://127.0.0.1:8000/docs