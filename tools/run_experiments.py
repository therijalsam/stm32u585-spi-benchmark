import shutil
import subprocess
from pathlib import Path


LATEST_RESULT = Path("results/benchmark.csv")
RUNS_DIRECTORY = Path("results/runs")


def next_run_file():
    RUNS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_number = 1

    while True:
        output_file = RUNS_DIRECTORY / f"benchmark_run_{run_number:03d}.csv"

        if not output_file.exists():
            return output_file

        run_number += 1


def run_single_experiment():
    subprocess.run(
        ["python3", "tools/capture_csv.py"],
        check=True,
    )

    output_file = next_run_file()

    shutil.copy2(
        LATEST_RESULT,
        output_file,
    )

    print(f"Saved experiment to {output_file}")


if __name__ == "__main__":
    run_single_experiment()