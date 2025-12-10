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
from utils import _process_file_afm, _download


def name(input_path, output_path):
    """
    Rename and copy PDB and JSON files with new naming convention.
    - Files with "_relaxed_" -> id_rank.pdb (e.g., Beta_endorphin-mu_opioid_001.pdb)
    - Files with "_scores_" -> id_rank.json (e.g., Beta_endorphin-mu_opioid_001.json)
    """
    os.makedirs(output_path, exist_ok=True)

    # Get all subdirectories
    subdirs = [
        d for d in os.listdir(input_path) if os.path.isdir(os.path.join(input_path, d))
    ]

    for subdir in subdirs:
        src_dir = os.path.join(input_path, subdir)

        # Process all files in the subdirectory
        for filename in os.listdir(src_dir):
            file_path = os.path.join(src_dir, filename)

            # Skip directories
            if os.path.isdir(file_path):
                continue

            # Process the file
            _process_file_afm(
                file_path, filename, output_path, pattern="_relaxed_", format="pdb"
            )
            _process_file_afm(
                file_path, filename, output_path, pattern="_scores_", format="json"
            )


def json_extract(json_path):
    """
    Extract key metrics from AlphaFold JSON file.

    Args:
        json_path (str): Path to the JSON file

    Returns:
        dict: Dictionary containing mean_plddt, max_pae, ptm, iptm, composite_ptm
    """
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        # Extract pLDDT scores
        plddt_list = data.get("plddt", [])
        mean_plddt = sum(plddt_list) / len(plddt_list) if plddt_list else 0.0

        max_pae = data.get("max_pae", 0.0)
        # Extract confidence metrics
        ptm = data.get("ptm", 0.0)
        iptm = data.get("iptm", 0.0)

        # Calculate composite PTM (0.8*iptm + 0.2*ptm)
        composite_ptm = 0.8 * iptm + 0.2 * ptm

        return {
            "plddt": round(mean_plddt, 3),
            "ptm": round(ptm, 3),
            "iptm": round(iptm, 3),
            "composite_ptm": round(composite_ptm, 3),
            "max_pae": round(max_pae, 3),
        }

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error processing {json_path}: {e}")
        return {
            "plddt": 0.00,
            "ptm": 0.00,
            "iptm": 0.00,
            "composite_ptm": 0.00,
            "max_pae": 0.00,
        }


def chain_extract(pdb_path):
    """
    Extract chain identifiers from a PDB file.

    Args:
        pdb_path (str): Path to the PDB file

    Returns:
        list: List of chain identifiers
    """
    chains = []
    try:
        with open(pdb_path, "r") as f:
            for line in f:
                if line.startswith("ATOM"):
                    chain_id = line[21]
                    if chain_id not in chains:
                        chains.append(chain_id)
    except FileNotFoundError as e:
        print(f"Error processing {pdb_path}: {e}")
    return chains


def build_afm_argparser():
    parser = argparse.ArgumentParser(description="AFMultimer Benchmark Model")

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


def main_afm(path, output_dir, url):
    tmp = os.getcwd() + "/tmp"
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    if url:
        _download(path, tmp)
        input_dir = os.path.join(tmp, "models/AFMultimer")
    else:
        input_dir = os.path.join(path, "AFMultimer")
    # input_dir = os.path.join(tmp, "models/AFMultimer")
    name(input_dir, output_dir)
    json_files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    pdb_files = [f for f in os.listdir(output_dir) if f.endswith(".pdb")]

    all_results = []

    for json_file in json_files:
        json_path = os.path.join(output_dir, json_file)
        json_name = str(Path(json_file).stem)

        protein_id = "_".join(json_name.split("_")[:-1])
        rank = json_name.split("_")[-1]

        result = json_extract(json_path)
        result.update({"id": protein_id, "rank": rank})

        all_results.append(result)

    # Process PDB files for chain information
    chain_results = []
    for pdb_file in pdb_files:
        pdb_path = os.path.join(output_dir, pdb_file)
        pdb_name = str(Path(pdb_file).stem)

        protein_id = "_".join(pdb_name.split("_")[:-1])
        rank = pdb_name.split("_")[-1]
        chains = chain_extract(pdb_path)

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

    dfs.to_csv(os.path.join(output_dir, "AFMultimer_metadata.csv"), index=False)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    # repo_url = "https://github.com/pszgaspar/short_peptide_modeling_benchmark.git"
    # output_dir = "./tmp"
    # download(repo_url, output_dir)
    parser = build_afm_argparser()
    args = parser.parse_args()

    repo_url = args.path
    output_dir = args.output_dir
    main_afm(repo_url, output_dir)
