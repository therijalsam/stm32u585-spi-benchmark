import csv
import re
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter


REFINED_CROSSOVER = "--refined-crossover" in sys.argv[1:]

if REFINED_CROSSOVER:
    OUTPUT_FILE = Path("results/refined_crossover.csv")
    TABLE_FILE = Path("results/refined_crossover_table.txt")
    GRAPH_DIRECTORY = Path("results/refined_graphs")

    EXPECTED_ROWS = 36

    CARGO_COMMAND = [
        "cargo",
        "run",
        "--features",
        "refined-crossover",
    ]
else:
    OUTPUT_FILE = Path("results/benchmark.csv")
    TABLE_FILE = Path("results/benchmark_table.txt")
    GRAPH_DIRECTORY = Path("results/graphs")

    EXPECTED_ROWS = 72

    CARGO_COMMAND = [
        "cargo",
        "run",
    ]

FIELDNAMES = [
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
]

TABLE_HEADERS = [
    "SPI Freq (Hz)",
    "Method",
    "Payload (B)",
    "Iterations",
    "Total Bytes",
    "Elapsed (us)",
    "Elapsed Cycles",
    "Avg (us)",
    "Avg Cycles",
    "Min (us)",
    "Max (us)",
    "Throughput (B/s)",
]


def extract_number(line, label):
    match = re.search(rf"{re.escape(label)}: (\d+)", line)

    if match:
        return int(match.group(1))

    return None


def format_number(value):
    if value is None:
        return ""

    return f"{value:,}"


def write_pretty_table(rows):
    table_rows = []

    for row in rows:
        table_rows.append([
            format_number(row["spi_frequency_hz"]),
            row["method"],
            format_number(row["payload_bytes"]),
            format_number(row["iterations"]),
            format_number(row["total_bytes"]),
            format_number(row["total_elapsed_us"]),
            format_number(row["total_elapsed_cycles"]),
            format_number(row["average_us"]),
            format_number(row["average_cycles"]),
            format_number(row["min_us"]),
            format_number(row["max_us"]),
            format_number(row["throughput_bytes_per_second"]),
        ])

    widths = []

    for index, header in enumerate(TABLE_HEADERS):
        width = len(header)

        for row in table_rows:
            width = max(width, len(str(row[index])))

        widths.append(width)

    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    header = "| " + " | ".join(
        TABLE_HEADERS[index].ljust(widths[index])
        for index in range(len(TABLE_HEADERS))
    ) + " |"

    lines = [
        separator,
        header,
        separator,
    ]

    previous_frequency = None
    previous_method = None

    for row in table_rows:
        current_frequency = row[0]
        current_method = row[1]

        if previous_frequency is not None and current_frequency != previous_frequency:
            lines.append(separator)

        elif previous_method is not None and current_method != previous_method:
            lines.append(separator)

        formatted_row = "| " + " | ".join([
            row[0].rjust(widths[0]),
            row[1].ljust(widths[1]),
            row[2].rjust(widths[2]),
            row[3].rjust(widths[3]),
            row[4].rjust(widths[4]),
            row[5].rjust(widths[5]),
            row[6].rjust(widths[6]),
            row[7].rjust(widths[7]),
            row[8].rjust(widths[8]),
            row[9].rjust(widths[9]),
            row[10].rjust(widths[10]),
            row[11].rjust(widths[11]),
        ]) + " |"

        lines.append(formatted_row)

        previous_frequency = current_frequency
        previous_method = current_method

    lines.append(separator)

    TABLE_FILE.write_text("\n".join(lines) + "\n")

    print()
    print("\n".join(lines))


def rows_for_frequency(rows, frequency, method):
    return [
        row
        for row in rows
        if row["spi_frequency_hz"] == frequency
        and row["method"] == method
    ]


def generate_throughput_graph(rows, frequency):
    blocking = rows_for_frequency(rows, frequency, "blocking")
    dma = rows_for_frequency(rows, frequency, "dma")

    blocking.sort(key=lambda row: row["payload_bytes"])
    dma.sort(key=lambda row: row["payload_bytes"])

    blocking_payloads = [
        str(row["payload_bytes"])
        for row in blocking
    ]

    blocking_throughput = [
        row["throughput_bytes_per_second"]
        for row in blocking
    ]

    dma_payloads = [
        str(row["payload_bytes"])
        for row in dma
    ]

    dma_throughput = [
        row["throughput_bytes_per_second"]
        for row in dma
    ]

    plt.figure(figsize=(10, 6))

    plt.plot(
        blocking_payloads,
        blocking_throughput,
        marker="o",
        label="Blocking",
    )

    plt.plot(
        dma_payloads,
        dma_throughput,
        marker="o",
        label="DMA",
    )

    plt.title(
        f"SPI Throughput vs Payload Size - {frequency // 1_000_000} MHz"
    )

    plt.xlabel("Payload Size (bytes)")
    plt.ylabel("Throughput (bytes/s)")

    plt.gca().yaxis.set_major_formatter(
        StrMethodFormatter("{x:,.0f}")
    )

    plt.grid(True)
    plt.legend()

    plt.tight_layout()

    output_file = GRAPH_DIRECTORY / (
        f"throughput_{frequency // 1_000_000}mhz.png"
    )

    plt.savefig(
        output_file,
        dpi=200,
    )

    plt.close()


def generate_cycle_graph(rows, frequency):
    blocking = rows_for_frequency(rows, frequency, "blocking")
    dma = rows_for_frequency(rows, frequency, "dma")

    blocking.sort(key=lambda row: row["payload_bytes"])
    dma.sort(key=lambda row: row["payload_bytes"])

    blocking_payloads = [
        str(row["payload_bytes"])
        for row in blocking
    ]

    blocking_cycles = [
        row["average_cycles"]
        for row in blocking
    ]

    dma_payloads = [
        str(row["payload_bytes"])
        for row in dma
    ]

    dma_cycles = [
        row["average_cycles"]
        for row in dma
    ]

    plt.figure(figsize=(10, 6))

    plt.plot(
        blocking_payloads,
        blocking_cycles,
        marker="o",
        label="Blocking",
    )

    plt.plot(
        dma_payloads,
        dma_cycles,
        marker="o",
        label="DMA",
    )

    plt.title(
        f"SPI Elapsed Core Cycles vs Payload Size - {frequency // 1_000_000} MHz"
    )

    plt.xlabel("Payload Size (bytes)")
    plt.ylabel("Average Core Cycles per Transfer")

    plt.gca().yaxis.set_major_formatter(
        StrMethodFormatter("{x:,.0f}")
    )

    plt.grid(True)
    plt.legend()

    plt.tight_layout()

    output_file = GRAPH_DIRECTORY / (
        f"cycles_{frequency // 1_000_000}mhz.png"
    )

    plt.savefig(
        output_file,
        dpi=200,
    )

    plt.close()


def generate_graphs(rows):
    GRAPH_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    frequencies = sorted({
        row["spi_frequency_hz"]
        for row in rows
    })

    for frequency in frequencies:
        generate_throughput_graph(
            rows,
            frequency,
        )

        generate_cycle_graph(
            rows,
            frequency,
        )

    print()
    print(
        f"Saved {len(frequencies) * 2} graphs to {GRAPH_DIRECTORY}"
    )


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    GRAPH_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    process = subprocess.Popen(
        CARGO_COMMAND,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    current_frequency = None
    current_method = None
    current_result = {}

    rows = []

    try:
        for line in process.stdout:
            print(line, end="")

            if "Actual SPI frequency:" in line:
                current_frequency = extract_number(
                    line,
                    "Actual SPI frequency",
                )

            elif "Starting blocking SPI benchmarks" in line:
                current_method = "blocking"

            elif "Starting DMA SPI benchmarks" in line:
                current_method = "dma"

            elif "DMA payload size:" in line:
                current_result = {
                    "spi_frequency_hz": current_frequency,
                    "method": current_method,
                    "payload_bytes": extract_number(
                        line,
                        "DMA payload size",
                    ),
                }

            elif "Payload size:" in line:
                current_result = {
                    "spi_frequency_hz": current_frequency,
                    "method": current_method,
                    "payload_bytes": extract_number(
                        line,
                        "Payload size",
                    ),
                }

            elif "Iterations:" in line and current_result:
                current_result["iterations"] = extract_number(
                    line,
                    "Iterations",
                )

            elif "Total bytes:" in line and current_result:
                current_result["total_bytes"] = extract_number(
                    line,
                    "Total bytes",
                )

            elif "Total elapsed time:" in line and current_result:
                current_result["total_elapsed_us"] = extract_number(
                    line,
                    "Total elapsed time",
                )

            elif "Total elapsed core cycles:" in line and current_result:
                current_result["total_elapsed_cycles"] = extract_number(
                    line,
                    "Total elapsed core cycles",
                )

            elif "Average core cycles per transfer:" in line and current_result:
                current_result["average_cycles"] = extract_number(
                    line,
                    "Average core cycles per transfer",
                )

            elif "Aggregate average time per transfer:" in line and current_result:
                current_result["average_us"] = extract_number(
                    line,
                    "Aggregate average time per transfer",
                )

            elif "Measured minimum time per transfer:" in line and current_result:
                current_result["min_us"] = extract_number(
                    line,
                    "Measured minimum time per transfer",
                )

            elif "Measured maximum time per transfer:" in line and current_result:
                current_result["max_us"] = extract_number(
                    line,
                    "Measured maximum time per transfer",
                )

            elif "DMA throughput:" in line and current_result:
                current_result["throughput_bytes_per_second"] = extract_number(
                    line,
                    "DMA throughput",
                )

                rows.append(current_result)
                current_result = {}

            elif "Throughput:" in line and current_result:
                current_result["throughput_bytes_per_second"] = extract_number(
                    line,
                    "Throughput",
                )

                rows.append(current_result)
                current_result = {}

            if "Benchmark complete" in line and "for" not in line:
                break

    finally:
        process.terminate()

        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()

    with OUTPUT_FILE.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()
        writer.writerows(rows)

    write_pretty_table(rows)

    generate_graphs(rows)

    print()
    print(f"Saved {len(rows)} benchmark rows to {OUTPUT_FILE}")
    print(f"Saved formatted benchmark table to {TABLE_FILE}")
    print(f"Saved benchmark graphs to {GRAPH_DIRECTORY}")

    if len(rows) == EXPECTED_ROWS:
        print("Benchmark export completed successfully.")
    else:
        print(
            f"Error: expected {EXPECTED_ROWS} rows but captured {len(rows)}."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()