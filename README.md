# GoQuest Manager

GoQuest Manager is a command-line tool for bulk creating and managing resources (Projects, Cycles, Modules, Issues) in a [Plane](https://plane.so/) instance. It uses YAML templates to define a hierarchy of resources and synchronizes their state with a local PostgreSQL database. This allows for reliable batch operations, tracking, and cleanup.

## Features

- **Bulk Creation**: Create entire project structures from a single YAML file.
- **State Synchronization**: Keeps track of all created Plane resources in a local database.
- **Transactional Operations**: Manages creation in batches, allowing for easy cleanup and rollbacks.
- **Hierarchical Structure**: Supports creating projects, cycles, modules, issues, and sub-issues.
- **Declarative Templates**: Define your project structure in an intuitive and readable YAML format.

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
    This command sets up the necessary tables in the PostgreSQL database.
    ```bash
    docker-compose run --rm app python main.py initdb
    ```

5.  **Create Resources**
    Run the `create` command with a template file. An example is provided in `data/batch_template.yaml`.
    ```bash
    docker-compose run --rm app python main.py create data/batch_template.yaml
    ```
    Take note of the `batch_id` output after the command succeeds.

6.  **Clean Up Resources (Optional)**
    To delete all resources created in a specific batch, use the `cleanup` command with the corresponding `batch_id`.
    ```bash
    docker-compose run --rm app python main.py cleanup <your_batch_id>
    ```

7.  **Stop Services**
    When you are finished, stop and remove the containers.
    ```bash
    docker-compose down
    ```

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
    ```bash
    python main.py testdb
    python main.py initdb
    ```

6.  **Run Commands**
    You can now use the CLI directly.
    ```bash
    # Create resources
    python main.py create data/batch_template.yaml

    # Clean up resources
    python main.py cleanup <your_batch_id>
    ```
