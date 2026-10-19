import csv
import shutil
import subprocess
import sys
from pathlib import Path


REFINED_CROSSOVER = "--refined-crossover" in sys.argv[1:]

if REFINED_CROSSOVER:
    LATEST_RESULT = Path("results/refined_crossover.csv")
    RUNS_DIRECTORY = Path("results/refined_runs")
    COMBINED_RESULTS = Path("results/refined_crossover_runs.csv")
    RUN_FILE_PREFIX = "refined_crossover_run"

    CAPTURE_COMMAND = [
        "python3",
        "tools/capture_csv.py",
        "--refined-crossover",
    ]
else:
    LATEST_RESULT = Path("results/benchmark.csv")
    RUNS_DIRECTORY = Path("results/runs")
    COMBINED_RESULTS = Path("results/benchmark_runs.csv")
    RUN_FILE_PREFIX = "benchmark_run"

    CAPTURE_COMMAND = [
        "python3",
        "tools/capture_csv.py",
    ]


def next_run_file():
    RUNS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_number = 1

    while True:
        output_file = RUNS_DIRECTORY / (
            f"{RUN_FILE_PREFIX}_{run_number:03d}.csv"
        )

        if not output_file.exists():
            return output_file

        run_number += 1


def append_run_to_dataset(run_file):
    run_number = int(
        run_file.stem.split("_")[-1]
    )

    with run_file.open(
        newline="",
    ) as source_file:
        reader = csv.DictReader(
            source_file,
        )

        fieldnames = [
            "run_id",
            *reader.fieldnames,
        ]

        write_header = not COMBINED_RESULTS.exists()

        with COMBINED_RESULTS.open(
            "a",
            newline="",
        ) as combined_file:
            writer = csv.DictWriter(
                combined_file,
                fieldnames=fieldnames,
            )

            if write_header:
                writer.writeheader()

            for row in reader:
                writer.writerow({
                    "run_id": run_number,
                    **row,
                })


def run_single_experiment():
    subprocess.run(
        CAPTURE_COMMAND,
        check=True,
    )

    output_file = next_run_file()

    shutil.copy2(
        LATEST_RESULT,
        output_file,
    )

    append_run_to_dataset(
        output_file,
    )

    print(f"Saved experiment to {output_file}")
    print(f"Updated combined dataset at {COMBINED_RESULTS}")


def run_experiments(run_count):
    for run in range(1, run_count + 1):
        print()
        print(f"Starting experiment {run} of {run_count}")

        run_single_experiment()


if __name__ == "__main__":
    arguments = [
        argument
        for argument in sys.argv[1:]
        if argument != "--refined-crossover"
    ]

    if len(arguments) != 1:
        print(
            "Usage: python3 tools/run_experiments.py "
            "<run_count> [--refined-crossover]"
        )
        sys.exit(1)

    run_count = int(
        arguments[0]
    )

    if run_count <= 0:
        print("Run count must be greater than zero.")
        sys.exit(1)

    run_experiments(
        run_count,
    )