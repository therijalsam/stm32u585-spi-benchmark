# STM32U585 SPI Performance Benchmark

Embedded Rust benchmarking framework for comparing **blocking SPI and DMA-backed SPI** on the STM32U585.

Built and tested on the **MM6108-EKH05** using **Rust, Embassy, STM32U585, DMA, DWT hardware cycle counting, RTT, probe-rs, and Python-based statistical analysis**.

The framework measures transfer latency, throughput, timing variation, elapsed
core cycles, task concurrency, SPI clock scaling, blocking-to-DMA crossover
behavior, and repeated-run statistical performance.

---

## Key Results

In a representative hardware run at **8 MHz SPI with a 256-byte payload**:

| Transfer Method | Throughput | Avg. Elapsed Cycles / Transfer |
|:----------------|-----------:|-------------------------------:|
| Blocking | 287,211 B/s | 14,261 |
| DMA | **853,390 B/s** | **4,800** |

In that representative run, DMA achieved approximately **197% higher
throughput** than blocking SPI.

The benchmark also observed a blocking-to-DMA crossover between **16 and
24 bytes** at both **4 MHz and 8 MHz**.

![8 MHz SPI Throughput](results/graphs/throughput_8mhz.png)

These values describe a representative single benchmark run.

For research analysis, the complete 72-configuration benchmark is repeated
independently 30 times. Mean throughput, sample standard deviation, 95%
confidence intervals, and crossover consistency are calculated from the
repeated-run dataset.

---

## Main Findings

- Blocking SPI performs better for very small transfers.
- DMA becomes significantly faster as payload size and SPI frequency increase.
- At 1 MHz and 2 MHz, blocking remained faster across the tested payload range in the representative run.
- At 4 MHz and 8 MHz, DMA overtook blocking between tested payload sizes.
- Blocking throughput began to plateau at higher SPI clock frequencies.
- DMA continued to scale strongly with SPI frequency.
- Embassy tasks continued executing while asynchronous DMA transfers were waiting for completion.
- The background task did not progress while blocking transfers were active.
- Cortex-M DWT measurements closely matched expected elapsed core-clock cycles.
- Repeated-run statistical analysis measures both average performance and run-to-run variability.
- Blocking-to-DMA crossover intervals are evaluated independently for each hardware run.

---

## Hardware

| Component | Configuration |
|:----------|:--------------|
| Board | MM6108-EKH05 |
| MCU | STM32U585AI |
| Core | ARM Cortex-M33 |
| Debug Probe | ST-LINK V3 |
| System Clock | 16 MHz HSI |
| SPI Peripheral | SPI1 |
| Maximum Tested SPI Clock | 8 MHz |

### SPI1 Pins

| Signal | Pin |
|:-------|:----|
| SCK | PE13 |
| MISO | PE14 |
| MOSI | PE15 |
| CS | PE12 |

Chip select is controlled in software using PE12.

---

## Benchmark Configuration

The benchmark currently tests:

```text
SPI frequencies:
1 MHz
2 MHz
4 MHz
8 MHz

Payload sizes:
4
16
24
32
40
48
56
64
256 bytes

Transfer methods:
blocking
DMA

Iterations per configuration:
100
```

One complete hardware benchmark contains:

```text
4 SPI frequencies
×
9 payload sizes
×
2 transfer methods
=
72 benchmark measurements
```

The repeated research experiment contains:

```text
30 independent runs
×
72 measurements
=
2,160 benchmark measurements
```

---

## What the Benchmark Measures

The firmware benchmark measures:

- aggregate transfer time
- average transfer time
- minimum transfer time
- maximum transfer time
- throughput
- total transferred bytes
- total elapsed Cortex-M cycles
- average elapsed cycles per transfer
- blocking SPI performance
- DMA-backed SPI performance
- multiple payload sizes
- multiple SPI frequencies
- blocking-to-DMA crossover behavior
- application task concurrency during DMA transfers

The host analysis additionally measures:

- repeated-run mean throughput
- sample standard deviation
- 95% confidence interval for mean throughput
- per-run blocking-to-DMA crossover interval
- crossover interval frequency
- crossover consistency percentage

---

## Representative Performance Results

The following tables show results from a representative hardware run.

### Blocking Throughput

| SPI Clock | 4 B | 16 B | 64 B | 256 B |
|----------:|----:|-----:|-----:|------:|
| 1 MHz | 79,856 B/s | 109,656 B/s | 120,670 B/s | 123,909 B/s |
| 2 MHz | 124,649 B/s | 199,750 B/s | 235,216 B/s | 246,118 B/s |
| 4 MHz | 154,083 B/s | 237,706 B/s | 275,482 B/s | 286,828 B/s |
| 8 MHz | 161,420 B/s | 242,314 B/s | 276,912 B/s | 287,211 B/s |

### DMA Throughput

| SPI Clock | 4 B | 16 B | 64 B | 256 B |
|----------:|----:|-----:|-----:|------:|
| 1 MHz | 63,724 B/s | 100,927 B/s | 117,963 B/s | 122,150 B/s |
| 2 MHz | 85,251 B/s | 169,294 B/s | 224,490 B/s | 239,918 B/s |
| 4 MHz | 85,070 B/s | 221,514 B/s | 408,919 B/s | 472,307 B/s |
| 8 MHz | 85,269 B/s | 221,208 B/s | 595,792 B/s | **853,390 B/s** |

### Blocking vs DMA

| SPI Clock | 4 B | 16 B | 64 B | 256 B |
|----------:|:----|:-----|:-----|:------|
| 1 MHz | Blocking +25% | Blocking +8% | Blocking +2% | Blocking +1% |
| 2 MHz | Blocking +46% | Blocking +17% | Blocking +4% | Blocking +2% |
| 4 MHz | Blocking +81% | Blocking +7% | DMA +48% | DMA +64% |
| 8 MHz | Blocking +89% | Blocking +9% | DMA +115% | **DMA +197%** |

The results demonstrate that DMA is not automatically faster than blocking
SPI.

For small transfers, DMA setup and synchronization overhead can exceed the
benefit of offloading the transfer.

As payload size and SPI frequency increase, DMA becomes progressively more
advantageous.

---

## Throughput Visualization

### 1 MHz

![1 MHz SPI Throughput](results/graphs/throughput_1mhz.png)

### 2 MHz

![2 MHz SPI Throughput](results/graphs/throughput_2mhz.png)

### 4 MHz

![4 MHz SPI Throughput](results/graphs/throughput_4mhz.png)

### 8 MHz

![8 MHz SPI Throughput](results/graphs/throughput_8mhz.png)

---

## DMA Crossover Analysis

The benchmark includes intermediate payload sizes to observe the transition
between blocking and DMA performance.

The representative run produced:

| SPI Clock | Observed Crossover |
|----------:|:-------------------|
| 1 MHz | No crossover detected |
| 2 MHz | No crossover detected |
| 4 MHz | Between 16 and 24 bytes |
| 8 MHz | Between 16 and 24 bytes |

At 8 MHz:

| Payload | Blocking | DMA | Faster |
|--------:|---------:|----:|:-------|
| 16 B | 242,314 B/s | 221,208 B/s | Blocking |
| 24 B | 256,602 B/s | 330,487 B/s | DMA |
| 32 B | 264,397 B/s | 413,597 B/s | DMA |
| 40 B | 269,305 B/s | 474,383 B/s | DMA |
| 48 B | 272,680 B/s | 524,762 B/s | DMA |
| 56 B | 275,143 B/s | 552,649 B/s | DMA |
| 64 B | 276,912 B/s | 595,792 B/s | DMA |

The framework reports a crossover interval rather than an exact threshold
because only explicitly configured payload sizes are measured.

---

## Repeated-Run Crossover Analysis

The crossover detector is also applied independently to every repeated hardware
run.

For each combination of:

```text
run_id
+
SPI frequency
```

the analysis compares blocking and DMA throughput across increasing payload
sizes.

A crossover is recorded when:

```text
blocking throughput >= DMA throughput
```

at one measured payload size, followed by:

```text
DMA throughput > blocking throughput
```

at the next measured payload size.

The repeated-run analysis currently summarizes crossover behavior at:

```text
4 MHz
8 MHz
```

The complete measured crossover distribution is exported to:

```text
results/crossover_statistics.csv
```

The file contains:

```text
spi_frequency_hz
crossover_lower_bytes
crossover_upper_bytes
run_count
total_runs
percentage
```

This allows the single-run crossover observation to be evaluated for
consistency across independent experiments instead of assuming one run
represents all hardware behavior.

---

## Cortex-M DWT Cycle Measurement

The benchmark uses the Cortex-M **Data Watchpoint and Trace (DWT)** cycle
counter alongside microsecond timing.

For every benchmark configuration it records:

- total elapsed core cycles
- average elapsed core cycles per transfer

### Representative 256-Byte Results

| SPI Clock | Blocking Cycles / Transfer | DMA Cycles / Transfer |
|----------:|---------------------------:|----------------------:|
| 1 MHz | 33,056 | 33,532 |
| 2 MHz | 16,643 | 17,073 |
| 4 MHz | 14,280 | 8,672 |
| 8 MHz | 14,261 | **4,800** |

### Cycle Graphs

#### 1 MHz

![1 MHz Core Cycles](results/graphs/cycles_1mhz.png)

#### 2 MHz

![2 MHz Core Cycles](results/graphs/cycles_2mhz.png)

#### 4 MHz

![4 MHz Core Cycles](results/graphs/cycles_4mhz.png)

#### 8 MHz

![8 MHz Core Cycles](results/graphs/cycles_8mhz.png)

At 8 MHz, the representative 256-byte DMA benchmark transferred 25,600 bytes
in approximately:

```text
29,998 us
```

The DWT recorded approximately:

```text
480,019 elapsed core cycles
```

With a 16 MHz system clock:

```text
29,998 us × 16 cycles/us ≈ 479,968 cycles
```

which closely matches the measured DWT value.

### DWT Interpretation

The DWT value represents **elapsed core-clock cycles** between the beginning and
end of the measured benchmark interval.

During asynchronous DMA transfers, this interval includes periods where the
benchmark task is suspended while waiting for DMA completion.

Therefore, the DWT measurement is not interpreted as CPU utilization and does
not represent only the instructions executed directly by the benchmark task.

---

## DMA Concurrency

A background Embassy task increments a counter approximately once per
millisecond while the benchmark executes.

```rust
#[embassy_executor::task]
async fn cpu_activity_task() {
    loop {
        CPU_ACTIVITY.fetch_add(1, Ordering::Relaxed);
        Timer::after_millis(1).await;
    }
}
```

Representative task progress:

| SPI Clock | Blocking | DMA |
|----------:|---------:|----:|
| 1 MHz | 0 | 854 |
| 2 MHz | 0 | 454 |
| 4 MHz | 0 | 257 |
| 8 MHz | 0 | 178 |

The background task made no progress while blocking transfers were active.

During asynchronous DMA transfers, the executor was able to schedule other
application work while the transfer waited for completion.

This demonstrates concurrency.

It should not be interpreted as a CPU utilization percentage.

---

## Firmware Architecture

The project separates hardware-specific SPI implementation from benchmark
logic through small transfer interfaces.

```rust
pub trait SpiTransfer {
    fn write(
        &mut self,
        data: &[u8],
    ) -> Result<(), embassy_stm32::spi::Error>;
}

pub trait DmaTransfer {
    async fn write_dma(
        &mut self,
        data: &[u8],
    ) -> Result<(), embassy_stm32::spi::Error>;
}
```

The blocking interface uses the synchronous SPI implementation.

The DMA interface uses Embassy's asynchronous SPI transfer support.

This separation allows benchmark logic to operate independently of the
hardware-specific implementation.

---

## Project Structure

```text
.
├── Cargo.toml
├── build.rs
├── memory.x
├── README.md
│
├── src
│   ├── main.rs
│   ├── benchmark.rs
│   ├── cycle_counter.rs
│   ├── spi.rs
│   ├── timer.rs
│   └── transfer.rs
│
├── tools
│   ├── capture_csv.py
│   ├── run_experiments.py
│   └── analyze_results.py
│
└── results
    ├── benchmark.csv
    ├── benchmark_table.txt
    ├── benchmark_runs.csv
    ├── throughput_statistics.csv
    ├── crossover_statistics.csv
    │
    ├── runs
    │   ├── benchmark_run_001.csv
    │   ├── benchmark_run_002.csv
    │   ├── ...
    │   └── benchmark_run_030.csv
    │
    └── graphs
        ├── throughput_1mhz.png
        ├── throughput_2mhz.png
        ├── throughput_4mhz.png
        ├── throughput_8mhz.png
        ├── cycles_1mhz.png
        ├── cycles_2mhz.png
        ├── cycles_4mhz.png
        └── cycles_8mhz.png
```

---

## Main Components

### `spi.rs`

Responsible for:

- SPI1 configuration
- blocking SPI transfers
- asynchronous DMA-backed transfers
- software chip select
- runtime SPI frequency configuration

### `benchmark.rs`

Responsible for:

- repeated transfer execution
- elapsed-time measurement
- throughput calculation
- timing statistics
- DWT cycle collection

### `cycle_counter.rs`

Responsible for:

- Cortex-M DWT initialization
- cycle-counter access
- elapsed-cycle calculation

### `transfer.rs`

Defines the hardware-independent interfaces used by the benchmark engine.

### `tools/capture_csv.py`

Responsible for:

- launching one complete hardware benchmark
- capturing RTT output
- parsing benchmark measurements
- writing the latest benchmark CSV
- producing the formatted benchmark table
- generating throughput graphs
- generating cycle-count graphs

### `tools/run_experiments.py`

Responsible for:

- executing multiple independent complete hardware benchmarks
- accepting a run count from the command line
- preserving each completed run
- selecting sequential run numbers automatically
- preventing previous runs from being overwritten
- adding each run to the combined repeated-run dataset
- preserving a `run_id` for each experiment

### `tools/analyze_results.py`

Responsible for:

- loading `results/benchmark_runs.csv`
- validating required CSV fields
- validating the number of measurements in each run
- grouping measurements by SPI frequency, method, and payload size
- calculating mean throughput
- calculating sample standard deviation
- calculating two-sided 95% confidence intervals using Student's t distribution
- detecting blocking-to-DMA crossover intervals independently for each run
- summarizing crossover consistency
- exporting throughput statistics
- exporting crossover statistics

---

## Benchmark Data

### Latest Single Run

The latest benchmark run is stored in:

```text
results/benchmark.csv
```

A human-readable version is stored in:

```text
results/benchmark_table.txt
```

The raw benchmark fields are:

```text
spi_frequency_hz
method
payload_bytes
iterations
total_bytes
total_elapsed_us
total_elapsed_cycles
average_us
average_cycles
min_us
max_us
throughput_bytes_per_second
```

---

## Repeated Research Dataset

Individual repeated runs are stored under:

```text
results/runs/
```

using sequential filenames:

```text
benchmark_run_001.csv
benchmark_run_002.csv
benchmark_run_003.csv
...
benchmark_run_030.csv
```

The combined dataset is stored in:

```text
results/benchmark_runs.csv
```

It adds a `run_id` field to the normal benchmark fields:

```text
run_id,spi_frequency_hz,method,payload_bytes,...
```

The current repeated dataset contains:

```text
30 independent runs
×
72 configurations
=
2,160 benchmark measurements
```

Preserving the individual run identifier allows variability between independent
experiments to be analyzed instead of combining all measurements as though
they came from one benchmark execution.

---

## Throughput Statistics

Repeated-run throughput statistics are exported to:

```text
results/throughput_statistics.csv
```

Each row represents one benchmark configuration.

The output fields are:

```text
spi_frequency_hz
method
payload_bytes
sample_count
mean_throughput_bytes_per_second
standard_deviation_bytes_per_second
confidence_interval_95_lower_bytes_per_second
confidence_interval_95_upper_bytes_per_second
```

There are:

```text
4 frequencies
×
9 payload sizes
×
2 methods
=
72 statistical configurations
```

Each configuration contains 30 independent measurements.

---

## Statistical Method

For one benchmark configuration, let the repeated throughput measurements be:

```text
x1, x2, x3, ..., xn
```

where:

```text
n = 30
```

### Mean

The arithmetic mean is:

```text
x̄ = (x1 + x2 + ... + xn) / n
```

The mean estimates the average measured throughput for that configuration.

### Sample Standard Deviation

The sample standard deviation is:

```text
s = sqrt(Σ(xi - x̄)^2 / (n - 1))
```

The use of `n - 1` treats the collected runs as a sample of possible repeated
measurements rather than as the complete population of all possible runs.

### Standard Error

The standard error of the mean is:

```text
SE = s / sqrt(n)
```

### 95% Confidence Interval

The two-sided 95% confidence interval is calculated as:

```text
x̄ ± t(0.975, n - 1) × SE
```

For 30 independent runs:

```text
n = 30
degrees of freedom = 29
```

The Student's t distribution is used because the population variance is not
known and is estimated from a finite sample of repeated hardware runs.

The confidence interval describes uncertainty in the estimated mean throughput.

It is not a guarantee that 95% of individual SPI transfers will lie within the
reported interval.

---

## Crossover Statistics

Repeated-run crossover statistics are exported to:

```text
results/crossover_statistics.csv
```

The fields are:

```text
spi_frequency_hz
crossover_lower_bytes
crossover_upper_bytes
run_count
total_runs
percentage
```

For example, a row containing:

```text
8000000,16,24,...
```

represents runs where blocking was still at least as fast as DMA at 16 bytes,
while DMA became faster at 24 bytes.

If no crossover is detected for a run, the crossover interval is represented
without lower and upper payload boundaries.

The statistical summary allows crossover stability to be evaluated across the
30 independent experiments.

The measured counts and percentages are kept in
`results/crossover_statistics.csv` so the repository's reported crossover
distribution is derived directly from the experiment data.

---

## Generate Results

Install the Python dependencies:

```bash
sudo apt install python3-matplotlib python3-scipy
```

### One Hardware Run

Run:

```bash
python3 tools/capture_csv.py
```

The utility runs the firmware through `cargo run`, captures RTT output, and
regenerates:

```text
results/benchmark.csv
results/benchmark_table.txt

results/graphs/throughput_1mhz.png
results/graphs/throughput_2mhz.png
results/graphs/throughput_4mhz.png
results/graphs/throughput_8mhz.png

results/graphs/cycles_1mhz.png
results/graphs/cycles_2mhz.png
results/graphs/cycles_4mhz.png
results/graphs/cycles_8mhz.png
```

---

## Collect Repeated Experiments

Run:

```bash
python3 tools/run_experiments.py 30
```

The argument controls the number of complete independent benchmark runs.

Each run contains all 72 measurement configurations.

Individual runs are preserved as:

```text
results/runs/benchmark_run_001.csv
results/runs/benchmark_run_002.csv
...
```

The next available run number is selected automatically.

Each completed run is also appended to:

```text
results/benchmark_runs.csv
```

with its corresponding `run_id`.

---

## Run Statistical Analysis

Run:

```bash
python3 tools/analyze_results.py
```

The analysis pipeline is:

```text
results/benchmark_runs.csv
        ↓
load repeated measurements
        ↓
validate required fields
        ↓
validate 72 measurements per run
        ↓
group matching configurations
        ↓
calculate mean throughput
        ↓
calculate sample standard deviation
        ↓
calculate standard error
        ↓
calculate 95% Student's t confidence interval
        ↓
detect crossover interval for each run
        ↓
summarize crossover consistency
        ↓
write statistical result files
```

Generated outputs:

```text
results/throughput_statistics.csv
results/crossover_statistics.csv
```

For 30 complete runs, successful loading and validation reports:

```text
Loaded 2160 benchmark measurements from 30 independent runs.
Validated 30 runs with 72 measurements each.
```

---

## Build

Install the embedded target:

```bash
rustup target add thumbv8m.main-none-eabihf
```

Build:

```bash
cargo build
```

Build optimized firmware:

```bash
cargo build --release
```

---

## Flash and Run

Connect the MM6108-EKH05 through ST-LINK.

Run:

```bash
cargo run
```

`probe-rs` flashes the STM32U585 and displays `defmt` output through RTT.

A representative result includes information such as:

```text
Requested SPI frequency: 8000000 Hz
Actual SPI frequency: 8000000 Hz

Payload size: 256 bytes
Iterations: 100

Blocking throughput: 287211 bytes/s
DMA throughput: 853390 bytes/s

Faster method: DMA
DMA throughput improvement: 197%

DMA crossover detected between 16 and 24 bytes
```

---

## Release Firmware

Build optimized firmware with:

```bash
cargo build --release
```

The ELF executable is generated under:

```text
target/thumbv8m.main-none-eabihf/release/
```

Firmware release artifacts can include:

```text
spi-benchmark.elf
spi-benchmark.bin
spi-benchmark.hex
```

The ELF file preserves debugging information.

BIN and HEX files can be used for direct firmware flashing.

Benchmark CSV files can be distributed alongside the firmware when
reproducibility of the measured results is required.

---

## Technologies

- Rust
- Embedded Rust
- Embassy
- STM32U585
- ARM Cortex-M33
- SPI
- DMA
- Cortex-M DWT
- asynchronous embedded programming
- probe-rs
- ST-LINK
- defmt
- RTT
- Python
- CSV
- Python statistics
- SciPy
- Matplotlib
- Git
- GitHub

---

## Development Workflow

The project was developed incrementally using feature branches.

Major completed features include:

```text
benchmark timing
SPI initialization
blocking SPI
transfer abstraction
repeated benchmarking
throughput calculation
multiple payload sizes
transfer timing statistics
DMA SPI
DMA benchmarking
DMA concurrency testing
automatic blocking/DMA comparison
SPI clock scaling
DMA crossover detection
DWT core-cycle measurement
CSV export
benchmark visualization
repeated experiment capture
combined repeated-run dataset
dataset validation
mean throughput analysis
sample standard deviation analysis
95% confidence interval analysis
per-run crossover analysis
crossover consistency analysis
```

Each major firmware feature was built and tested on the STM32U585 before being
merged into `main`.

Research analysis is performed from preserved raw benchmark measurements so
derived statistical results can be reproduced from the repository data.

---

## Why This Project

This project explores an important embedded-systems engineering question:

> When does the additional complexity of DMA provide a measurable advantage
> over a simple blocking SPI transfer?

DMA is often described as the faster or more efficient approach, but the actual
trade-off depends on several factors.

For small payloads, DMA configuration, synchronization, interrupt handling, and
software overhead may outweigh the time saved by hardware-assisted transfer.

For larger payloads, especially at higher peripheral frequencies, DMA can
provide substantially higher throughput while also allowing other asynchronous
tasks to make progress.

This benchmark measures that transition experimentally rather than assuming a
fixed answer.

The repeated-run experiment extends the analysis beyond a single measurement by
quantifying:

```text
average performance
run-to-run variability
uncertainty in the estimated mean
blocking-to-DMA crossover consistency
```

This provides a stronger basis for evaluating when DMA is beneficial on the
STM32U585 with Embassy-based embedded Rust firmware.