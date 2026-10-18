import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev

from scipy.stats import t as student_t


INPUT_FILE = Path("results/benchmark_runs.csv")
STATISTICS_FILE = Path("results/throughput_statistics.csv")
CROSSOVER_STATISTICS_FILE = Path("results/crossover_statistics.csv")

EXPECTED_MEASUREMENTS_PER_RUN = 72
CONFIDENCE_LEVEL = 0.95

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


def calculate_throughput_statistics(rows):
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

    statistics = {}

    for key, values in throughput_groups.items():
        sample_count = len(values)
        mean_value = mean(values)
        standard_deviation = stdev(values)

        degrees_of_freedom = sample_count - 1

        critical_value = student_t.ppf(
            1 - (1 - CONFIDENCE_LEVEL) / 2,
            degrees_of_freedom,
        )

        standard_error = (
            standard_deviation
            / math.sqrt(sample_count)
        )

        margin_of_error = (
            critical_value
            * standard_error
        )

        statistics[key] = {
            "mean": mean_value,
            "standard_deviation": standard_deviation,
            "sample_count": sample_count,
            "confidence_lower": mean_value - margin_of_error,
            "confidence_upper": mean_value + margin_of_error,
        }

    return statistics


def detect_run_crossovers(rows):
    measurements = defaultdict(
        lambda: defaultdict(dict)
    )

    for row in rows:
        run_id = int(
            row["run_id"]
        )

        frequency = int(
            row["spi_frequency_hz"]
        )

        method = row["method"]

        payload = int(
            row["payload_bytes"]
        )

        throughput = int(
            row["throughput_bytes_per_second"]
        )

        measurements[
            (run_id, frequency)
        ][method][payload] = throughput

    crossovers = []

    for key in sorted(measurements):
        run_id, frequency = key
        methods = measurements[key]

        blocking = methods["blocking"]
        dma = methods["dma"]

        payloads = sorted(
            set(blocking)
            & set(dma)
        )

        crossover = None

        for lower_payload, upper_payload in zip(
            payloads,
            payloads[1:],
        ):
            blocking_faster_at_lower = (
                blocking[lower_payload]
                >= dma[lower_payload]
            )

            dma_faster_at_upper = (
                dma[upper_payload]
                > blocking[upper_payload]
            )

            if (
                blocking_faster_at_lower
                and dma_faster_at_upper
            ):
                crossover = (
                    lower_payload,
                    upper_payload,
                )

                break

        crossovers.append({
            "run_id": run_id,
            "frequency": frequency,
            "crossover": crossover,
        })

    return crossovers


def summarize_crossovers(crossovers):
    target_frequencies = (
        4_000_000,
        8_000_000,
    )

    summary = {}

    for frequency in target_frequencies:
        frequency_results = [
            result
            for result in crossovers
            if result["frequency"] == frequency
        ]

        counts = Counter(
            result["crossover"]
            for result in frequency_results
        )

        summary[frequency] = {
            "total_runs": len(frequency_results),
            "counts": counts,
        }

    return summary


def write_throughput_statistics(statistics):
    with STATISTICS_FILE.open(
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
            "sample_count",
            "mean_throughput_bytes_per_second",
            "standard_deviation_bytes_per_second",
            "confidence_interval_95_lower_bytes_per_second",
            "confidence_interval_95_upper_bytes_per_second",
        ])

        for key in sorted(statistics):
            frequency, method, payload = key
            result = statistics[key]

            writer.writerow([
                frequency,
                method,
                payload,
                result["sample_count"],
                f'{result["mean"]:.2f}',
                f'{result["standard_deviation"]:.2f}',
                f'{result["confidence_lower"]:.2f}',
                f'{result["confidence_upper"]:.2f}',
            ])


def write_crossover_statistics(summary):
    with CROSSOVER_STATISTICS_FILE.open(
        "w",
        newline="",
    ) as file:
        writer = csv.writer(
            file,
        )

        writer.writerow([
            "spi_frequency_hz",
            "crossover_lower_bytes",
            "crossover_upper_bytes",
            "run_count",
            "total_runs",
            "percentage",
        ])

        for frequency in sorted(summary):
            total_runs = summary[frequency]["total_runs"]
            counts = summary[frequency]["counts"]

            sorted_counts = sorted(
                counts.items(),
                key=lambda item: (
                    item[0] is None,
                    item[0] or (0, 0),
                ),
            )

            for crossover, count in sorted_counts:
                if crossover is None:
                    lower_payload = ""
                    upper_payload = ""
                else:
                    lower_payload, upper_payload = crossover

                percentage = (
                    count
                    / total_runs
                    * 100
                )

                writer.writerow([
                    frequency,
                    lower_payload,
                    upper_payload,
                    count,
                    total_runs,
                    f"{percentage:.2f}",
                ])


def print_crossover_summary(summary):
    print()
    print("DMA crossover consistency:")

    for frequency in sorted(summary):
        total_runs = summary[frequency]["total_runs"]
        counts = summary[frequency]["counts"]

        print()
        print(f"{frequency} Hz:")

        sorted_counts = sorted(
            counts.items(),
            key=lambda item: (
                item[0] is None,
                item[0] or (0, 0),
            ),
        )

        for crossover, count in sorted_counts:
            percentage = (
                count
                / total_runs
                * 100
            )

            if crossover is None:
                crossover_text = "No crossover"
            else:
                lower_payload, upper_payload = crossover

                crossover_text = (
                    f"{lower_payload}-"
                    f"{upper_payload} bytes"
                )

            print(
                f"  {crossover_text}: "
                f"{count}/{total_runs} runs "
                f"({percentage:.2f}%)"
            )


def main():
    rows, run_ids = load_results()

    run_counts = validate_run_sizes(
        rows,
    )

    statistics = calculate_throughput_statistics(
        rows,
    )

    crossovers = detect_run_crossovers(
        rows,
    )

    crossover_summary = summarize_crossovers(
        crossovers,
    )

    write_throughput_statistics(
        statistics,
    )

    write_crossover_statistics(
        crossover_summary,
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
    print("Throughput statistics by configuration:")

    for key in sorted(statistics):
        frequency, method, payload = key
        result = statistics[key]

        print(
            f"{frequency} Hz, "
            f"{method}, "
            f"{payload} bytes: "
            f"mean={result['mean']:.2f} B/s, "
            f"std={result['standard_deviation']:.2f} B/s, "
            f"95% CI=[{result['confidence_lower']:.2f}, "
            f"{result['confidence_upper']:.2f}] B/s, "
            f"n={result['sample_count']}"
        )

    print()
    print("Per-run DMA crossover intervals:")

    for result in crossovers:
        if result["frequency"] not in (
            4_000_000,
            8_000_000,
        ):
            continue

        crossover = result["crossover"]

        if crossover is None:
            crossover_text = "none"
        else:
            lower_payload, upper_payload = crossover

            crossover_text = (
                f"{lower_payload}-"
                f"{upper_payload} bytes"
            )

        print(
            f"run={result['run_id']}, "
            f"frequency={result['frequency']} Hz, "
            f"crossover={crossover_text}"
        )

    print_crossover_summary(
        crossover_summary,
    )

    print()
    print(
        f"Saved throughput statistics to "
        f"{STATISTICS_FILE}"
    )

    print(
        f"Saved crossover statistics to "
        f"{CROSSOVER_STATISTICS_FILE}"
    )


if __name__ == "__main__":
    main()