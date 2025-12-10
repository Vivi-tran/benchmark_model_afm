import argparse
import sys
from pathlib import Path
import tarfile
import shutil

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from afm import main_afm
from chai1 import main_chai1
from helixfold3 import main_helixfold3
from native.download import retrieve_natives

def build_argparser():
    parser = argparse.ArgumentParser(description="AFM Benchmark Model")

    parser.add_argument(
        "--input_path", 
        default="https://github.com/pszgaspar/short_peptide_modeling_benchmark.git",
        type=str, 
        help="GitHub repository URL to download the dataset or local path.")

    parser.add_argument(
        "--model",
        choices=["AFMultimer", "Chai-1", "HelixFold3"],
        default="AFMultimer",
        help="Choose the model type to process (default: AFMultimer)"
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        type=str,
        help="Directory to save the processed dataset.",
    )
    parser.add_argument(
        '--name',
        choices=["AFMultimer", "Chai-1", "HelixFold3"],
        default='AFm',
        help='Name for omnibenchmark. Default: AFm'
    )

    parser.add_argument(
        "--input",
        type=str,
        default="./native_metadata.csv",
        help="Path to input csv file with columns <id>, <pdb_id>.",
    )
    return parser

def main():
    parser = build_argparser()
    args = parser.parse_args()

    input_path = args.input_path
    model = args.model
    output_model = Path(args.output_dir) / model

    if isinstance(input_path, str) and input_path.startswith("https://github.com/"):
        repo_url = input_path
        url = True
        # Download and process model results from repo
        if model == "AFMultimer":
            main_afm(repo_url, str(output_model), url=url)
        elif model == "Chai-1":
            main_chai1(repo_url, str(output_model), url=url)
        elif model == "HelixFold3":
            main_helixfold3(repo_url, str(output_model), url=url)
    elif input_path and Path(input_path).exists():
        # Process local path directly
        url = False
        if model == "AFMultimer":
            main_afm(input_path, str(output_model), url=url)
        elif model == "Chai-1":
            main_chai1(input_path, str(output_model), url=url)
        elif model == "HelixFold3":
            main_helixfold3(input_path, str(output_model), url=url)
    else:
        raise ValueError("input_path must be a valid GitHub repo URL or an existing local path.")
    # Create tar archive
    archive_name = output_model.parent / f"{args.name}.tar"
    with tarfile.open(archive_name, "w") as tar:
        tar.add(output_model, arcname=output_model.name)
    if archive_name.exists():
        shutil.rmtree(output_model)

    # Download native structures
    output_native = Path(args.output_dir) / "natives"
    retrieve_natives(args.input, output_native)
    shutil.copy2(args.input, output_native / Path(args.input).name)

    # Create tar archive
    archive_name = output_native.parent / f"{args.name}.{output_native.name}.tar"
    with tarfile.open(archive_name, "w") as tar:
        tar.add(output_native, arcname=output_native.name)
    if archive_name.exists():
        shutil.rmtree(output_native)


if __name__ == "__main__":
    main()
