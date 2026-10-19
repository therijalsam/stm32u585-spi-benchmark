import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter


INPUT_FILE = Path("results/refined_throughput_statistics.csv")
GRAPH_DIRECTORY = Path("results/refined_statistical_graphs")

TARGET_FREQUENCIES = (
    4_000_000,
    8_000_000,
)

REQUIRED_FIELDS = {
    "spi_frequency_hz",
    "method",
    "payload_bytes",
    "sample_count",
    "mean_throughput_bytes_per_second",
    "standard_deviation_bytes_per_second",
    "confidence_interval_95_lower_bytes_per_second",
    "confidence_interval_95_upper_bytes_per_second",
}


def load_statistics():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Refined statistics file not found: {INPUT_FILE}"
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

        rows = list(
            reader
        )

    return rows


def organize_statistics(rows):
    organized = defaultdict(
        lambda: defaultdict(list)
    )

    for row in rows:
        frequency = int(
            row["spi_frequency_hz"]
        )

        method = row[
            "method"
        ]

        payload = int(
            row["payload_bytes"]
        )

        mean_throughput = float(
            row[
                "mean_throughput_bytes_per_second"
            ]
        )

        confidence_lower = float(
            row[
                "confidence_interval_95_lower_bytes_per_second"
            ]
        )

        confidence_upper = float(
            row[
                "confidence_interval_95_upper_bytes_per_second"
            ]
        )

        organized[
            frequency
        ][method].append({
            "payload": payload,
            "mean": mean_throughput,
            "confidence_lower": confidence_lower,
            "confidence_upper": confidence_upper,
        })

    for frequency in organized:
        for method in organized[frequency]:
            organized[
                frequency
            ][method].sort(
                key=lambda result: result["payload"]
            )

    return organized


def calculate_error_bars(results):
    lower_errors = [
        result["mean"]
        - result["confidence_lower"]
        for result in results
    ]

    upper_errors = [
        result["confidence_upper"]
        - result["mean"]
        for result in results
    ]

    return [
        lower_errors,
        upper_errors,
    ]


def generate_frequency_graph(
    frequency,
    blocking_results,
    dma_results,
):
    payloads = [
        result["payload"]
        for result in blocking_results
    ]

    blocking_means = [
        result["mean"]
        for result in blocking_results
    ]

    dma_means = [
        result["mean"]
        for result in dma_results
    ]

    blocking_errors = calculate_error_bars(
        blocking_results
    )

    dma_errors = calculate_error_bars(
        dma_results
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.errorbar(
        payloads,
        blocking_means,
        yerr=blocking_errors,
        marker="o",
        capsize=4,
        label="Blocking",
    )

    plt.errorbar(
        payloads,
        dma_means,
        yerr=dma_errors,
        marker="o",
        capsize=4,
        label="DMA",
    )

    plt.title(
        f"Refined SPI Crossover - "
        f"{frequency // 1_000_000} MHz"
    )

    plt.xlabel(
        "Payload Size (bytes)"
    )

    plt.ylabel(
        "Mean Throughput (bytes/s)"
    )

    plt.xticks(
        payloads
    )

    plt.gca().yaxis.set_major_formatter(
        StrMethodFormatter(
            "{x:,.0f}"
        )
    )

    plt.grid(
        True
    )

    plt.legend()

    plt.tight_layout()

    output_file = GRAPH_DIRECTORY / (
        f"refined_crossover_"
        f"{frequency // 1_000_000}mhz.png"
    )

    plt.savefig(
        output_file,
        dpi=200,
    )

    plt.close()

    print(
        f"Saved refined crossover graph to "
        f"{output_file}"
    )


def generate_graphs(rows):
    GRAPH_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    organized = organize_statistics(
        rows
    )

    for frequency in TARGET_FREQUENCIES:
        frequency_results = organized[
            frequency
        ]

        blocking_results = frequency_results[
            "blocking"
        ]

        dma_results = frequency_results[
            "dma"
        ]

        generate_frequency_graph(
            frequency,
            blocking_results,
            dma_results,
        )


def main():
    rows = load_statistics()

    generate_graphs(
        rows
    )


if __name__ == "__main__":
    main()