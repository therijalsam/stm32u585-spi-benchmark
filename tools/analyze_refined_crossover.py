import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev

from scipy.stats import t as student_t


INPUT_FILE = Path("results/refined_crossover_runs.csv")
STATISTICS_FILE = Path("results/refined_throughput_statistics.csv")
CROSSOVER_FILE = Path("results/refined_crossover_statistics.csv")
PAIRED_DIFFERENCE_FILE = Path(
    "results/refined_paired_difference_statistics.csv"
)

EXPECTED_MEASUREMENTS_PER_RUN = 36
CONFIDENCE_LEVEL = 0.95

TARGET_FREQUENCIES = (
    4_000_000,
    8_000_000,
)

REFINED_PAYLOAD_SIZES = (
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
)

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
            f"Refined crossover dataset not found: {INPUT_FILE}"
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

    return rows


def validate_run_sizes(rows):
    run_counts = Counter(
        int(row["run_id"])
        for row in rows
    )

    invalid_runs = {
        run_id: count
        for run_id, count in run_counts.items()
        if count != EXPECTED_MEASUREMENTS_PER_RUN
    }

    if invalid_runs:
        details = ", ".join(
            f"run {run_id}: {count} measurements"
            for run_id, count in sorted(invalid_runs.items())
        )

        raise ValueError(
            f"Invalid refined run sizes detected: {details}"
        )

    return run_counts


def validate_configurations(rows):
    configurations = defaultdict(
        set
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

        configurations[run_id].add((
            frequency,
            method,
            payload,
        ))

    expected = {
        (
            frequency,
            method,
            payload,
        )
        for frequency in TARGET_FREQUENCIES
        for method in (
            "blocking",
            "dma",
        )
        for payload in REFINED_PAYLOAD_SIZES
    }

    invalid_runs = []

    for run_id, actual in configurations.items():
        if actual != expected:
            invalid_runs.append(
                run_id
            )

    if invalid_runs:
        run_list = ", ".join(
            str(run_id)
            for run_id in sorted(invalid_runs)
        )

        raise ValueError(
            f"Unexpected refined benchmark configurations "
            f"in runs: {run_list}"
        )


def calculate_confidence_interval(
    values,
):
    sample_count = len(
        values
    )

    mean_value = mean(
        values
    )

    standard_deviation = stdev(
        values
    )

    degrees_of_freedom = (
        sample_count - 1
    )

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

    return {
        "sample_count": sample_count,
        "mean": mean_value,
        "standard_deviation": standard_deviation,
        "confidence_lower": mean_value - margin_of_error,
        "confidence_upper": mean_value + margin_of_error,
    }


def calculate_throughput_statistics(rows):
    throughput_groups = defaultdict(
        list
    )

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
        statistics[key] = calculate_confidence_interval(
            values
        )

    return statistics


def calculate_paired_difference_statistics(rows):
    measurements = defaultdict(
        dict
    )

    for row in rows:
        run_id = int(
            row["run_id"]
        )

        frequency = int(
            row["spi_frequency_hz"]
        )

        payload = int(
            row["payload_bytes"]
        )

        method = row["method"]

        throughput = int(
            row["throughput_bytes_per_second"]
        )

        measurements[
            (
                run_id,
                frequency,
                payload,
            )
        ][method] = throughput

    difference_groups = defaultdict(
        list
    )

    for key in sorted(measurements):
        run_id, frequency, payload = key

        methods = measurements[
            key
        ]

        if (
            "blocking" not in methods
            or "dma" not in methods
        ):
            raise ValueError(
                f"Missing paired transfer measurement for "
                f"run {run_id}, frequency {frequency}, "
                f"payload {payload}"
            )

        difference = (
            methods["dma"]
            - methods["blocking"]
        )

        difference_groups[
            (
                frequency,
                payload,
            )
        ].append(
            difference
        )

    statistics = {}

    for key, differences in difference_groups.items():
        result = calculate_confidence_interval(
            differences
        )

        if result["confidence_lower"] > 0:
            interpretation = "dma_faster"
        elif result["confidence_upper"] < 0:
            interpretation = "blocking_faster"
        else:
            interpretation = "uncertain"

        result[
            "interpretation"
        ] = interpretation

        statistics[
            key
        ] = result

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

        crossover = None

        for lower_payload, upper_payload in zip(
            REFINED_PAYLOAD_SIZES,
            REFINED_PAYLOAD_SIZES[1:],
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
    summary = {}

    for frequency in TARGET_FREQUENCIES:
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


def write_paired_difference_statistics(
    statistics,
):
    with PAIRED_DIFFERENCE_FILE.open(
        "w",
        newline="",
    ) as file:
        writer = csv.writer(
            file,
        )

        writer.writerow([
            "spi_frequency_hz",
            "payload_bytes",
            "sample_count",
            "mean_dma_minus_blocking_bytes_per_second",
            "standard_deviation_bytes_per_second",
            "confidence_interval_95_lower_bytes_per_second",
            "confidence_interval_95_upper_bytes_per_second",
            "interpretation",
        ])

        for key in sorted(statistics):
            frequency, payload = key
            result = statistics[key]

            writer.writerow([
                frequency,
                payload,
                result["sample_count"],
                f'{result["mean"]:.2f}',
                f'{result["standard_deviation"]:.2f}',
                f'{result["confidence_lower"]:.2f}',
                f'{result["confidence_upper"]:.2f}',
                result["interpretation"],
            ])


def write_crossover_statistics(summary):
    with CROSSOVER_FILE.open(
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
            total_runs = summary[
                frequency
            ]["total_runs"]

            counts = summary[
                frequency
            ]["counts"]

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
    print("Refined DMA crossover consistency:")

    for frequency in sorted(summary):
        total_runs = summary[
            frequency
        ]["total_runs"]

        counts = summary[
            frequency
        ]["counts"]

        print()
        print(
            f"{frequency} Hz:"
        )

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
                crossover_text = (
                    "No crossover"
                )
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


def print_paired_difference_summary(
    statistics,
):
    print()
    print(
        "Paired DMA - Blocking throughput analysis:"
    )

    for frequency in TARGET_FREQUENCIES:
        print()
        print(
            f"{frequency} Hz:"
        )

        for payload in REFINED_PAYLOAD_SIZES:
            result = statistics[
                (
                    frequency,
                    payload,
                )
            ]

            print(
                f"  {payload} bytes: "
                f"mean difference="
                f"{result['mean']:.2f} B/s, "
                f"95% CI=["
                f"{result['confidence_lower']:.2f}, "
                f"{result['confidence_upper']:.2f}] B/s, "
                f"{result['interpretation']}"
            )


def print_supported_dma_thresholds(
    statistics,
):
    print()
    print(
        "First tested payload with statistically "
        "supported DMA advantage:"
    )

    for frequency in TARGET_FREQUENCIES:
        supported_payload = None

        for payload in REFINED_PAYLOAD_SIZES:
            result = statistics[
                (
                    frequency,
                    payload,
                )
            ]

            if (
                result["confidence_lower"]
                > 0
            ):
                supported_payload = payload

                break

        if supported_payload is None:
            print(
                f"  {frequency} Hz: "
                f"none in tested range"
            )
        else:
            print(
                f"  {frequency} Hz: "
                f"{supported_payload} bytes"
            )


def main():
    rows = load_results()

    run_counts = validate_run_sizes(
        rows,
    )

    validate_configurations(
        rows,
    )

    statistics = calculate_throughput_statistics(
        rows,
    )

    paired_statistics = (
        calculate_paired_difference_statistics(
            rows
        )
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

    write_paired_difference_statistics(
        paired_statistics,
    )

    write_crossover_statistics(
        crossover_summary,
    )

    print(
        f"Loaded {len(rows)} refined benchmark measurements "
        f"from {len(run_counts)} independent runs."
    )

    print(
        f"Validated {len(run_counts)} runs with "
        f"{EXPECTED_MEASUREMENTS_PER_RUN} measurements each."
    )

    print()
    print("Refined throughput statistics:")

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

    print_paired_difference_summary(
        paired_statistics,
    )

    print_supported_dma_thresholds(
        paired_statistics,
    )

    print_crossover_summary(
        crossover_summary,
    )

    print()
    print(
        f"Saved refined throughput statistics to "
        f"{STATISTICS_FILE}"
    )

    print(
        f"Saved paired throughput differences to "
        f"{PAIRED_DIFFERENCE_FILE}"
    )

    print(
        f"Saved refined crossover statistics to "
        f"{CROSSOVER_FILE}"
    )


if __name__ == "__main__":
    main()