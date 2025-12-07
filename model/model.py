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

    # Download and process model results
    repo_url = "https://github.com/pszgaspar/short_peptide_modeling_benchmark.git"
    model = args.model
    output_model = Path(args.output_dir) / model
    if model == "AFMultimer":
        main_afm(repo_url, str(output_model))

    elif model == "Chai-1":
        main_chai1(repo_url, str(output_model))
    elif model == "HelixFold3":
        main_helixfold3(repo_url, str(output_model))
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
    archive_name = output_native.parent / f"{output_native.name}.tar"
    with tarfile.open(archive_name, "w") as tar:
        tar.add(output_native, arcname=output_native.name)
    if archive_name.exists():
        shutil.rmtree(output_native)


if __name__ == "__main__":
    main()
