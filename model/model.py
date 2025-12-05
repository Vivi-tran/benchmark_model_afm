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

    return parser


# def main():
#     parser = build_argparser()
#     args = parser.parse_args()

#     repo_url = "https://github.com/pszgaspar/short_peptide_modeling_benchmark.git"
#     model = args.model
#     output_dir = Path(args.output_dir) / model
#     if model == "AFMultimer":
#         main_afm(repo_url, output_dir)

#     elif model == "Chai-1":
#         main_chai1(repo_url, output_dir)
#     elif model == "HelixFold3":
#         main_helixfold3(repo_url, output_dir)
#     # Create tar.gz archive
#     archive_name = output_dir.parent / f"{output_dir.name}.tar.gz"
#     with tarfile.open(archive_name, "w:gz") as tar:
#         tar.add(output_dir, arcname=output_dir.name)
#     if archive_name.exists():
#         shutil.rmtree(output_dir) 

def main():
    parser = build_argparser()
    args = parser.parse_args()

    repo_url = "https://github.com/pszgaspar/short_peptide_modeling_benchmark.git"
    model = args.model
    output_dir = Path(args.output_dir) / model
    if model == "AFMultimer":
        main_afm(repo_url, str(output_dir))

    elif model == "Chai-1":
        main_chai1(repo_url, str(output_dir))
    elif model == "HelixFold3":
        main_helixfold3(repo_url, str(output_dir))
    # Create tar archive
    archive_name = output_dir.parent / f"{output_dir.name}.tar"
    with tarfile.open(archive_name, "w") as tar:
        tar.add(output_dir, arcname=output_dir.name)
    if archive_name.exists():
        shutil.rmtree(output_dir)  


if __name__ == "__main__":
    main()
