# GoQuest Manager

GoQuest Manager is a service for bulk creating and managing resources (Projects, Cycles, Modules, Issues) in a [Plane](https://plane.so/) instance. It uses a FastAPI server to accept YAML templates and synchronizes their state with a local PostgreSQL database. This allows for reliable batch operations, tracking, and cleanup.

## Features

- **API-Driven**: Exposes a FastAPI endpoint to create entire project structures from a single YAML file.
- **State Synchronization**: Keeps track of all created Plane resources in a local database.
- **Transactional Operations**: Manages creation in batches, allowing for easy tracking.
- **Hierarchical Structure**: Supports creating projects, cycles, modules, issues, and sub-issues.
- **Declarative Templates**: Define your project structure in an intuitive and readable YAML format.
- **Automatic API Docs**: Interactive API documentation powered by Swagger UI.

---

## Quick Setup (Docker Compose)

This is the recommended method for running the application.

### Prerequisites

- Docker
- Docker Compose

### Instructions

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd goquest_manager
    ```

2.  **Configure Environment**
    Copy the example `.env` file and fill in your Plane API details.
    ```bash
    cp .env.example .env
    ```
    Now, edit `.env` and add your `PLANE_API_KEY` and `PLANE_WORKSPACE_SLUG`.

3.  **Start the Database**
    ```bash
    docker-compose up -d db
    ```

4.  **Initialize the Application Database**
    This one-time command sets up the necessary tables in the PostgreSQL database.
    ```bash
    docker-compose run --rm app python -c "from src.models import init_db; init_db()"
    ```

5.  **Run the FastAPI Server**
    ```bash
    docker-compose up --build app
    ```
    The server will be accessible at `http://localhost:8000`.

---

## Local Development Setup

Follow these instructions to run the application directly on your local machine.

### Prerequisites

- Python 3.10+
- PostgreSQL (running locally or accessible on the network)

### Instructions

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd goquest_manager
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate
    # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Copy the example `.env` file.
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file with your details:
    -   Set `DB_HOST` to `localhost` (or your PostgreSQL host).
    -   Update `DB_USER`, `DB_PASSWORD`, and `DB_NAME` for your local database.
    -   Fill in your `PLANE_API_KEY` and `PLANE_WORKSPACE_SLUG`.

5.  **Initialize the Database**
    You can run this one-time setup command to initialize the database tables.
    ```bash
    python -c "from src.models import init_db; init_db()"
    ```

6.  **Run the FastAPI Server**
    You can now run the API server using Uvicorn.
    ```bash
    # host 0.0.0.0 to allow access from other machines
    # ex sample.com:8019 (if allow port forwarding & firewall 8019 open)
    uvicorn main:app --host 0.0.0.0 --port 8019
    ```
    The `--reload` flag automatically reloads the server when you make code changes.

---

## FastAPI Server

Once the server is running, you can interact with the API.

### Accessing API Documentation

The application provides automatically generated API documentation using Swagger UI. Once the server is running, navigate to the following URL in your browser:

[**http://127.0.0.1:8000/docs**](http://127.0.0.1:8000/docs)

Here, you can see all available endpoints, their parameters, and test them interactively directly in the browser.

### Creating Resources via API

To create resources, send a `POST` request to the `/create/` endpoint with your YAML template file.

An example template is provided at `data/batch_template.yaml`.

#### Example using `curl`

```bash
curl -X POST -F "file=@data/batch_template.yaml" http://127.0.0.1:8000/create/
```

#### Successful Response

A successful request will return a JSON response containing the batch information:

```json
{
  "message": "Resource creation process started successfully.",
  "batch_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "template_name": "Example Project Batch",
  "status": "RUNNING"
}
```

You can use the `batch_id` to track the created resources in the database.

