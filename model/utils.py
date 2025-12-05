import os, shutil, re


def _extract(filename, separator, pattern=r"_rank_(\d+)_"):
    """
    Extract ID and rank from filename based on separator.

    Returns:
        tuple: (id_part, rank) or (None, None) if not found
    """
    if separator not in filename:
        return None, None

    # Extract ID (part before separator)
    id_part = filename.split(separator)[0]

    # Extract rank using regex to find "_rank_XXX_" pattern
    rank_match = re.search(pattern, filename)
    if rank_match:
        return id_part, rank_match.group(1)

    return None, None


def _process_file(file_path, filename, output_path, pattern="_relaxed_", format="pdb"):
    """
    Process a single file for renaming and copying.

    Args:
        file_path: Full path to the file
        filename: Just the filename
        output_path: Output directory path
    """
    # Process PDB files with "_relaxed_"
    if pattern in filename and filename.endswith(f".{format}"):
        id_part, rank = _extract(filename, pattern)
        if id_part and rank:
            new_filename = f"{id_part}_{rank}.{format}"
            dst_path = os.path.join(output_path, new_filename)
            shutil.copy2(file_path, dst_path)


if __name__ == "__main__":
    pass
