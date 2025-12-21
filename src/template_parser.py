import yaml
from pathlib import Path
from src.schemas import BatchTemplate


def parse_template(template_path: Path) -> BatchTemplate:
    """
    Parses a YAML template file and validates it against the BatchTemplate schema.
    """
    try:
        with open(template_path, "r") as f:
            data = yaml.safe_load(f)
            return BatchTemplate.model_validate(data)
    except FileNotFoundError:
        print(f"Error: Template file not found at {template_path}")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during template parsing: {e}")
        raise
