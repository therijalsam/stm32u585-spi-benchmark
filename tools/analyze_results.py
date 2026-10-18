import csv
from collections import Counter, defaultdict
from pathlib import Path


INPUT_FILE = Path("results/benchmark_runs.csv")
MEAN_THROUGHPUT_FILE = Path("results/mean_throughput.csv")

EXPECTED_MEASUREMENTS_PER_RUN = 72

REQUIRED_FIELDS = {
    "run_id",
    "spi_frequency_hz",
    "method",
    "payload_bytes",
    "iterations",
    "total_bytes",
    "total_elapsed_us",
    "total_elapsed_cycles",
    "average_us",
    "average_cycles",
    "min_us",
    "max_us",
    "throughput_bytes_per_second",
}


def load_results():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Benchmark dataset not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
        )

        fieldnames = set(
            reader.fieldnames or []
        )

        missing_fields = REQUIRED_FIELDS - fieldnames

        if missing_fields:
            missing = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                f"Missing required CSV fields: {missing}"
            )

        rows = list(reader)

    run_ids = {
        int(row["run_id"])
        for row in rows
    }

    return rows, run_ids


def validate_run_sizes(rows):
    run_counts = Counter(
        int(row["run_id"])
        for row in rows
    )

    incomplete_runs = {
        run_id: count
        for run_id, count in run_counts.items()
        if count != EXPECTED_MEASUREMENTS_PER_RUN
    }

    if incomplete_runs:
        details = ", ".join(
            f"run {run_id}: {count} measurements"
            for run_id, count in sorted(incomplete_runs.items())
        )

        raise ValueError(
            f"Invalid run sizes detected: {details}"
        )

    return run_counts


def calculate_mean_throughput(rows):
    throughput_groups = defaultdict(list)

    for row in rows:
        key = (
            int(row["spi_frequency_hz"]),
            row["method"],
            int(row["payload_bytes"]),
        )

        throughput_groups[key].append(
            int(row["throughput_bytes_per_second"])
        )

    mean_throughput = {}

    for key, values in throughput_groups.items():
        mean_throughput[key] = sum(values) / len(values)

    return mean_throughput


def write_mean_throughput(mean_throughput):
    with MEAN_THROUGHPUT_FILE.open(
        "w",
        newline="",
    ) as file:
        writer = csv.writer(
            file,
        )

        writer.writerow([
            "spi_frequency_hz",
            "method",
            "payload_bytes",
            "mean_throughput_bytes_per_second",
        ])

        for key in sorted(mean_throughput):
            frequency, method, payload = key

            writer.writerow([
                frequency,
                method,
                payload,
                f"{mean_throughput[key]:.2f}",
            ])


def main():
    rows, run_ids = load_results()

    run_counts = validate_run_sizes(
        rows,
    )

    mean_throughput = calculate_mean_throughput(
        rows,
    )

    write_mean_throughput(
        mean_throughput,
    )

    print(
        f"Loaded {len(rows)} benchmark measurements "
        f"from {len(run_ids)} independent runs."
    )

    print(
        f"Validated {len(run_counts)} runs with "
        f"{EXPECTED_MEASUREMENTS_PER_RUN} measurements each."
    )

    print()
    print("Mean throughput by configuration:")

    for key in sorted(mean_throughput):
        frequency, method, payload = key

        print(
            f"{frequency} Hz, "
            f"{method}, "
            f"{payload} bytes: "
            f"{mean_throughput[key]:.2f} B/s"
        )

    print()
    print(
        f"Saved mean throughput results to "
        f"{MEAN_THROUGHPUT_FILE}"
    )


if __name__ == "__main__":
    main()