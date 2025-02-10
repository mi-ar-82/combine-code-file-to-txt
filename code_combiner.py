import os
import datetime
from pathlib import Path

# Function to parse .gitignore
def get_ignored_paths(gitignore_path):
    ignored = set()
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    ignored.add(line)
    return ignored

# Function to check if a file should be ignored
def is_ignored(path, ignored_paths):
    return (
        any(path.match(ignore) or any(part == ignore for part in path.parts) for ignore in ignored_paths) or
        any(part.startswith('.') for part in path.parts)  # Ignore hidden folders and files
    )

# Function to generate a tree-like folder map
def generate_folder_map(root, ignored_paths):
    def tree(dir_path, prefix=""):
        entries = sorted(
            [e for e in dir_path.iterdir() if not is_ignored(e.relative_to(root), ignored_paths)],
            key=lambda e: (e.is_file(), e.name)
        )
        folder_map = []
        for index, entry in enumerate(entries):
            connector = "└── " if index == len(entries) - 1 else "├── "
            folder_map.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if index == len(entries) - 1 else "│   "
                folder_map.extend(tree(entry, prefix + extension))
        return folder_map

    return "\n".join(tree(root))

# Function to concatenate code files
def concatenate_code_files(root, ignored_paths, folder_map):
    combined_code = ["# Folder Map\n", folder_map, "\n\n\n"]
    included_files = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out ignored and hidden directories
        dirnames[:] = [d for d in dirnames if not is_ignored(Path(dirpath) / d, ignored_paths)]

        for file in filenames:
            file_path = Path(dirpath) / file
            rel_path = file_path.relative_to(root)
            if not is_ignored(rel_path, ignored_paths) and file_path.suffix in {'.py', '.js', '.java', '.html', '.css'}:
                included_files.append(str(rel_path))
                combined_code.append("\n\n\n")  # Add minimum 3 empty lines between files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    combined_code.append(f"### File: {rel_path}\n")
                    combined_code.append(f.read())

    # Add included files list with 3 empty lines before
    combined_code.insert(2, "\n\n\n# Included Files\n" + "\n".join(included_files) + "\n\n\n")
    return "".join(combined_code)

# Main execution
if __name__ == "__main__":
    root_dir = Path(__file__).parent
    output_dir = root_dir / "output_code_combiner"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    code_output_file = output_dir / f"combined_code_{timestamp}.txt"

    ignored_paths = get_ignored_paths(root_dir / ".gitignore")

    # Generate folder map
    folder_map = generate_folder_map(root_dir, ignored_paths)

    # Concatenate code files with folder map at the beginning
    combined_code = concatenate_code_files(root_dir, ignored_paths, folder_map)
    with open(code_output_file, 'w', encoding='utf-8') as f:
        f.write(combined_code)

    print(f"Combined code with folder map saved to {code_output_file}")
