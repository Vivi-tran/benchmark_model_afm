import shutil
import json
import subprocess
import os, re
import pandas as pd
import argparse
from pathlib import Path
import sys

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils import _process_file_chai1, _download


def name(input_path, output_path):
    """
    Rename and copy PDB and JSON files with new naming convention.

    """
    os.makedirs(output_path, exist_ok=True)

    # Get all subdirectories
    subdirs = [
        d for d in os.listdir(input_path) if os.path.isdir(os.path.join(input_path, d))
    ]

    for subdir in subdirs:
        id = Path(subdir).name
        src_dir = os.path.join(input_path, subdir)

        # Process all files in the subdirectory
        for filename in os.listdir(src_dir):
            file_path = os.path.join(src_dir, filename)

            # Skip directories
            if os.path.isdir(file_path):
                continue
            
            # Process the file
            _process_file_chai1(
                id, file_path, filename, output_path, pattern=".rank_", format="cif"
            )
            _process_file_chai1(
                id, file_path, filename, output_path, pattern=".rank_", format="json"
            )


def json_extract(json_path):
    """
    Extract key metrics from JSON file.

    Args:
        json_path (str): Path to the JSON file

    Returns:
        dict: Dictionary containing mean_plddt, max_pae, ptm, iptm, composite_ptm
    """
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        # Extract pLDDT scores
        # plddt_list = data.get("plddt", [])
        # mean_plddt = sum(plddt_list) / len(plddt_list) if plddt_list else 0.0

        # max_pae = data.get("max_pae", 0.0)
        # Extract confidence metrics
        ptm = data.get("ptm", 0.0)
        iptm = data.get("iptm", 0.0)

        # Calculate composite PTM (0.8*iptm + 0.2*ptm)
        composite_ptm = data.get("aggregate_score", 0.0)

        return {
            "ptm": round(ptm, 3),
            "iptm": round(iptm, 3),
            "composite_ptm": round(composite_ptm, 3),
        }

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error processing {json_path}: {e}")
        return {
            "ptm": 0.00,
            "iptm": 0.00,
            "composite_ptm": 0.00,
        }


def chain_extract(cif_path):
    """
    More robust version using regex to extract chain information
    """
    
    chains = []
    
    try:
        with open(cif_path, 'r') as file:
            content = file.read()
            
        # Use regex to find entity details patterns
        pattern = r"^\d+\s+polymer\s+man\s+'Entity\s+([A-Z])'"
        matches = re.findall(pattern, content, re.MULTILINE)
        
        chains = matches
        
    except Exception as e:
        print(f"Error reading CIF file: {e}")
        return []
    
    return chains

def build_chai1_argparser():
    parser = argparse.ArgumentParser(description="Chai-1 Benchmark Model")

    parser.add_argument(
        "--path", required=True, type=str, help="Path to download the dataset."
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        type=str,
        help="Directory to save the processed dataset.",
    )
    return parser


def main_chai1(path, output_dir):
    tmp = os.getcwd() + "/tmp"
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    _download(path, tmp, folder_path="models/Chai-1")
    input_dir = os.path.join(tmp, "models/Chai-1")
    name(input_dir, output_dir)
    json_files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    cif_files = [f for f in os.listdir(output_dir) if f.endswith(".cif")]

    all_results = []

    for json_file in json_files:
        json_path = os.path.join(output_dir, json_file)
        json_name = str(Path(json_file).stem)

        protein_id = "_".join(json_name.split("_")[:-1])
        rank = json_name.split("_")[-1]

        result = json_extract(json_path)
        result.update({"id": protein_id, "rank": rank})

        all_results.append(result)

    # Process CIF files for chain information
    chain_results = []
    for cif_file in cif_files:
        cif_path = os.path.join(output_dir, cif_file)
        cif_name = str(Path(cif_file).stem)

        protein_id = "_".join(cif_name.split("_")[:-1])
        rank = cif_name.split("_")[-1]
        chains = chain_extract(cif_path)

        chain_results.append(
            {
                "id": protein_id,
                "rank": rank,
                "chains": "".join(chains)[:2],
            }
        )

    dfs = pd.DataFrame(all_results)
    chain_df = pd.DataFrame(chain_results)

    dfs = pd.merge(dfs, chain_df, on=["id", "rank"], how="left")

    try:
        main_cols = [
            "id",
            "rank",
            "chains",
        ]
        dfs = dfs[main_cols + [c for c in dfs.columns if c not in main_cols]]
        dfs.sort_values(by=["id", "rank"], inplace=True)
    except KeyError as e:
        print(f"Missing expected columns: {e}")
        print(f"Available columns: {list(dfs.columns)}")

    dfs.to_csv(os.path.join(output_dir, "Chai1_metadata.csv"), index=False)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    parser = build_chai1_argparser()
    args = parser.parse_args()
    main_chai1(args.path, args.output_dir)
    # python model/chai1.py --path https://github.com/pszgaspar/short_peptide_modeling_benchmark.git --output_dir data/processed/Chai-1
