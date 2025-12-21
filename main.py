import argparse
from pathlib import Path
import uuid
from src.engine import ExecutionEngine
from src.models import init_db, test_db_connection


def main():
    parser = argparse.ArgumentParser(description="Plane Bulk Operations Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Init DB command
    parser_initdb = subparsers.add_parser("initdb", help="Initialize the database")

    # Test DB command
    parser_testdb = subparsers.add_parser("testdb", help="Test the database connection")

    # Create command
    parser_create = subparsers.add_parser("create", help="Create resources from a template")
    parser_create.add_argument(
        "template_file", type=Path, help="Path to the YAML template file"
    )

    # Cleanup command
    parser_cleanup = subparsers.add_parser("cleanup", help="Cleanup resources from a batch")
    parser_cleanup.add_argument("batch_id", type=uuid.UUID, help="The UUID of the batch to clean up")

    args = parser.parse_args()
    engine = ExecutionEngine()

    if args.command == "initdb":
        print("Initializing database...")
        init_db()
        print("Database initialized.")
    elif args.command == "testdb":
        test_db_connection()
    elif args.command == "create":
        if not args.template_file.is_file():
            print(f"Error: Template file not found at {args.template_file}")
            return
        engine.run_creation(args.template_file)
    elif args.command == "cleanup":
        engine.run_cleanup(args.batch_id)


if __name__ == "__main__":
    main()
