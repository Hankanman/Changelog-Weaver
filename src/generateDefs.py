""" Generate dataclasses and enums from JSON files and create a master file. """

from pathlib import Path
from datamodel_code_generator import InputFileType, generate


def generate_dataclasses_from_json(input_json: str, output_file: str) -> None:
    """
    Generate dataclasses and enums from a JSON file and save to the specified output file.

    Args:
        input_json (str): Path to the input JSON file.
        output_file (str): Path to the output Python file.
    """
    input_path = Path(input_json)
    output_path = Path(output_file)

    generate(
        input_=input_path.read_text(encoding="utf-8"),
        input_file_type=InputFileType.Json,
        output=output_path,
    )
    print(f"Generated dataclasses and enums from {input_json}.")


def generate_definitions_and_master(
    input_folder: str, output_dir: str, master_file_path: str
) -> None:
    """
    Generate dataclass definitions for all JSON files in a folder and create a master file.

    Args:
        input_folder (str): Path to the folder containing JSON files.
        output_dir (str): Directory to store the generated Python files.
        master_file_path (str): Path to the master file that imports all generated files.
    """
    input_folder_path = Path(input_folder)
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    import_lines = []

    for json_file in input_folder_path.glob("*.json"):
        output_file = output_dir_path / f"{json_file.stem}.py"
        generate_dataclasses_from_json(str(json_file), str(output_file))

        module_name = output_file.stem
        import_lines.append(f"from .{module_name} import *")

    with open(master_file_path, "w", encoding="utf-8") as f:
        f.write('"""\nThis module imports all generated models.\n"""\n')
        f.write("\n".join(import_lines))
        f.write("\n\n__all__ = [")
        f.write(
            ", ".join(
                f'"{json_file.stem}"' for json_file in input_folder_path.glob("*.json")
            )
        )
        f.write("]\n")


if __name__ == "__main__":
    # Folder containing JSON files
    json_folder = "defs/json"

    # Directory to store the generated Python files
    output_directory = "defs"

    # Master file to import all generated files
    master_file = "defs/__init__.py"

    with open(master_file, "w", encoding="utf-8") as f:
        # Generate the dataclasses and the master file
        generate_definitions_and_master(json_folder, output_directory, master_file)

    print(
        f"Dataclasses and enums have been generated for each JSON file in {json_folder} and saved in {output_directory}."
    )
    print(f"A master file has been created at {master_file}.")
