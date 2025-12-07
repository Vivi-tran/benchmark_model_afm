import os, shutil, re
import subprocess


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
        return id_part, int(rank_match.group(1))

    return None, None


def _process_file_afm(file_path, filename, output_path, pattern="_relaxed_", format="pdb"):
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

def _process_file_chai1(id, file_path, filename, output_path, pattern=".rank_", format="cif"):
    """
    Process a single file for renaming and copying.

    Args:
        file_path: Full path to the file
        filename: Just the filename
        output_path: Output directory path
    """
    # Process PDB files with "_relaxed_"
    if filename.endswith(f".{format}"):
        rank = int(filename.split(pattern)[1].split(".")[0]) + 1
        if id and rank:
            new_filename = f"{id}_{rank}.{format}"
            dst_path = os.path.join(output_path, new_filename)
            shutil.copy2(file_path, dst_path)      



def _process_file_helixfold3(input_path, subdir_path, output_path):
    """Process individual job subdirectories within a main result folder"""
    subdir_name = os.path.basename(subdir_path)
    
    # Extract ID and rank from job directory name 
    if subdir_name.startswith("job-") and "-rank" in subdir_name:
        parts = subdir_name[4:]  # Remove "job-" prefix
        rank_index = parts.rfind("-rank")
        if rank_index != -1:
            ids = parts[:rank_index].split("-")[:-1]
            id = "-".join(ids)
            rank = parts[rank_index + 5:]

            json_src = os.path.join(subdir_path, "all_results.json")
            cif_src = os.path.join(subdir_path, "predicted_structure.cif")

            json_dst = os.path.join(output_path, f"{id}_{rank}.json")
            cif_dst = os.path.join(output_path, f"{id}_{rank}.cif")
            
            if os.path.exists(json_src):
                shutil.copy2(json_src, json_dst)
            if os.path.exists(cif_src):
                shutil.copy2(cif_src, cif_dst)


def _download(repo_url, destination, folder_path="models/AFMultimer"):
    """
    Download a specific folder using partial clone with tree filter.
    """
    try:
        # Create destination directory
        os.makedirs(destination, exist_ok=True)

        # Use partial clone with tree filter
        subprocess.run(
            [
                "git",
                "clone",
                "--filter=tree:0",
                "--no-checkout",
                repo_url,
                destination,
            ],
            check=True,
        )

        # Configure sparse-checkout
        subprocess.run(
            ["git", "config", "core.sparseCheckout", "true"],
            cwd=destination,
            check=True,
        )

        # Set sparse-checkout path
        sparse_checkout_file = os.path.join(
            destination, ".git", "info", "sparse-checkout"
        )
        with open(sparse_checkout_file, "w") as f:
            f.write(f"{folder_path}/*\n")

        # Checkout only the specified folder
        subprocess.run(["git", "checkout"], cwd=destination, check=True)

    except subprocess.CalledProcessError as e:
        print(f"Partial clone failed: {e}")
        raise

if __name__ == "__main__":
    pass
