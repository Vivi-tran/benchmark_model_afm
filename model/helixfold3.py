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
from utils import _process_file_helixfold3, _download


def name(input_path, output_path):
    """Process HelixFold3 results directory structure"""
    os.makedirs(output_path, exist_ok=True)
    
    # Get all main result directories (helixfold3_result_to_download_*)
    main_dirs = [
        d for d in os.listdir(input_path) 
        if os.path.isdir(os.path.join(input_path, d)) and d.startswith("helixfold3_result")
    ]
    
    for main_dir in main_dirs:
        main_dir_path = os.path.join(input_path, main_dir)
        
        # Get all job subdirectories within the main directory
        job_dirs = [
            d for d in os.listdir(main_dir_path)
            if os.path.isdir(os.path.join(main_dir_path, d)) and d.startswith("job-")
        ]
        
        for job_dir in job_dirs:
            job_dir_path = os.path.join(main_dir_path, job_dir)
            _process_file_helixfold3(input_path, job_dir_path, output_path)

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
        mean_plddt = data.get("mean_plddt", 0.0)
        global_pae = data.get("global_pae", 0.0)

        # Extract confidence metrics
        ptm = data.get("ptm", 0.0)
        iptm = data.get("iptm", 0.0)

        # Calculate composite PTM (0.8*iptm + 0.2*ptm)
        composite_ptm = data.get("ranking_confidence", 0.0)

        return {
            "mean_plddt": round(mean_plddt, 2),
            "global_pae": round(global_pae, 2),
            "ptm": round(ptm, 2),
            "iptm": round(iptm, 2),
            "composite_ptm": round(composite_ptm, 2),
        }

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error processing {json_path}: {e}")
        return {
            "mean_plddt": 0.00,
            "global_pae": 0.00,
            "ptm": 0.00,
            "iptm": 0.00,
            "composite_ptm": 0.00,
        }


def chain_extract(cif_path):
    """
    Extract chain IDs from CIF file using _entity_poly section with regex
    """
    
    chains = []
    
    try:
        with open(cif_path, 'r') as file:
            content = file.read()
            
        # Use regex to find lines in _entity_poly section
        # Pattern matches: number + chain_id + polypeptide(L)
        pattern = r'^\d+\s+([A-Z])\s+polypeptide\(L\)'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        chains = matches
        
    except Exception as e:
        print(f"Error reading CIF file: {e}")
        return []
    
    return chains

def build_helixfold3_argparser():
    parser = argparse.ArgumentParser(description="HelixFold3 Benchmark Model")

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


def main_helixfold3(path, output_dir):
    tmp = os.getcwd() + "/tmp"
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    _download(path, tmp, folder_path="models/HelixFold3")
    input_dir = os.path.join(tmp, "models/HelixFold3")
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

    dfs.to_csv(os.path.join(output_dir, "HelixFold3_metadata.csv"), index=False)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    parser = build_helixfold3_argparser()
    args = parser.parse_args()
    main_helixfold3(args.path, args.output_dir)
    # python model/helixfold3.py --path https://github.com/pszgaspar/short_peptide_modeling_benchmark.git --output_dir data/processed/HelixFold3
