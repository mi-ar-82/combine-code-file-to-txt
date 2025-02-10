#!/usr/bin/env python3
import os
import fnmatch
import datetime


def load_gitignore(gitignore_path = ".gitignore"):
    """
    Reads the .gitignore file and returns a list of ignore patterns.
    Comments and empty lines are skipped.
    """
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(path, patterns):
    """
    Checks if a given path matches any of the ignore patterns.
    Both the full relative path and the basename are checked.
    """
    for pattern in patterns:
        # If the pattern ends with a slash, treat it as a folder pattern.
        if pattern.endswith("/"):
            pattern = pattern.rstrip("/")
            if pattern in path.split(os.sep):
                return True
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False


def get_all_files(root, ignore_patterns):
    """
    Walks the root directory recursively and collects file paths that:
    • Do not match .gitignore patterns.
    • Are not hidden (do not start with a dot).
    """
    file_paths = []
    for current_dir, dirs, files in os.walk(root):
        rel_dir = os.path.relpath(current_dir, root)
        if rel_dir == ".":
            rel_dir = ""
        # Filter out directories that are hidden or ignored.
        dirs[:] = [d for d in dirs if not (d.startswith('.') or is_ignored(os.path.join(rel_dir, d), ignore_patterns))]
        for file in files:
            file_rel = os.path.join(rel_dir, file) if rel_dir else file
            if file.startswith('.') or is_ignored(file_rel, ignore_patterns):
                continue
            file_paths.append(os.path.join(current_dir, file))
    return file_paths


def combine_files(file_list):
    """
    Reads and concatenates the content of each file.
    Each file's content is prefixed with a header line showing its relative path.
    """
    combined_text = ""
    for file_path in sorted(file_list):
        rel_path = os.path.relpath(file_path)
        combined_text += f"\n# File: {rel_path}\n"
        try:
            with open(file_path, "r", encoding = "utf-8", errors = "ignore") as f:
                combined_text += f.read() + "\n"
        except Exception as e:
            combined_text += f"# [Error reading file: {e}]\n"
    return combined_text


def generate_tree_lines(current_dir, rel_path, prefix, ignore_patterns):
    """
    Recursively builds a list of strings representing the tree structure using
    ├── and └── connectors. Filters out hidden entries and those specified by ignore_patterns.
    """
    lines = []
    # Gather and sort entries filtering out hidden and ignored ones.
    entries = []
    for entry in sorted(os.listdir(current_dir)):
        full_rel = os.path.join(rel_path, entry) if rel_path else entry
        if entry.startswith('.') or is_ignored(full_rel, ignore_patterns):
            continue
        entries.append(entry)
    count = len(entries)
    for i, entry in enumerate(entries):
        is_last = (i == count - 1)
        connector = "└── " if is_last else "├── "
        line = prefix + connector + entry
        lines.append(line)
        full_path = os.path.join(current_dir, entry)
        if os.path.isdir(full_path):
            extension = "    " if is_last else "│   "
            new_prefix = prefix + extension
            new_rel = os.path.join(rel_path, entry) if rel_path else entry
            lines.extend(generate_tree_lines(full_path, new_rel, new_prefix, ignore_patterns))
    return lines


def generate_tree_map(root, ignore_patterns):
    """
    Generates a tree-like folder map for the project using the generate_tree_lines function.
    The header of the output is the project folder name.
    """
    header = os.path.basename(os.path.abspath(root))
    lines = [header]
    lines.extend(generate_tree_lines(root, "", "", ignore_patterns))
    return "\n".join(lines)


def main():
    # Load ignore patterns from .gitignore.
    ignore_patterns = load_gitignore()
    # Hardcode: ignore the output folder.
    output_folder = "output_code_combiner"
    if output_folder not in ignore_patterns:
        ignore_patterns.append(output_folder)

    root = "."
    # Get all file paths (excluding hidden and ignored files/folders).
    file_list = get_all_files(root, ignore_patterns)
    # Combine the contents of these files.
    concatenated_code = combine_files(file_list)
    # Generate the tree-like folder map with connectors.
    tree_map = generate_tree_map(root, ignore_patterns)
    # Create a sorted list of file paths included.
    file_list_text = "\n".join(sorted(os.path.relpath(path, root) for path in file_list))

    # Combine all sections in the specified order:
    # 1. Folder Tree Map
    # 2. List of Files Included
    # 3. Combined Code
    # Each section is separated by 4 empty lines.
    output_sections = [
        "########## Folder Tree Map ##########\n" + tree_map,
        "########## List of Files Included ##########\n" + file_list_text,
        "########## Combined Code ##########\n" + concatenated_code
    ]
    final_output_text = "\n\n\n\n".join(output_sections)

    # Create the output directory if it does not exist.
    output_dir = os.path.join(root, output_folder)
    os.makedirs(output_dir, exist_ok = True)

    # Generate a timestamped filename.
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"combined_output_{timestamp}.txt"
    output_filepath = os.path.join(output_dir, output_filename)

    # Write the final output to the file.
    with open(output_filepath, "w", encoding = "utf-8") as out_file:
        out_file.write(final_output_text)

    print("Code concatenation complete.")
    print(f"Output saved to: {output_filepath}")


if __name__ == "__main__":
    main()
