# STM32U585 SPI Performance Benchmark

Embedded Rust benchmarking framework for comparing **blocking SPI and DMA-backed SPI** on the STM32U585.

Built and tested on the **MM6108-EKH05** using **Rust, Embassy, STM32U585, DMA, DWT hardware cycle counting, RTT, and probe-rs**.

The framework measures transfer latency, throughput, timing variation, elapsed
core cycles, task concurrency, SPI clock scaling, and the payload size where
DMA begins to outperform blocking SPI.

---

## Key Results

At **8 MHz SPI with a 256-byte payload** in a representative hardware run:

| Transfer Method | Throughput | Avg. Elapsed Cycles / Transfer |
|:----------------|-----------:|-------------------------------:|
| Blocking | 287,211 B/s | 14,261 |
| DMA | **853,390 B/s** | **4,800** |

DMA achieved approximately **197% higher throughput** than blocking SPI in this
representative run.

The benchmark also found a blocking-to-DMA crossover between **16 and 24 bytes**
at both **4 MHz and 8 MHz**.

![8 MHz SPI Throughput](results/graphs/throughput_8mhz.png)

### Main Findings

- Blocking SPI performs better for very small transfers.
- DMA becomes significantly faster as payload size and SPI frequency increase.
- At 1 MHz and 2 MHz, blocking remained faster across the tested payload range.
- At 4 MHz and 8 MHz, DMA overtook blocking between 16 and 24 bytes.
- Blocking throughput began to plateau at higher SPI clock frequencies.
- DMA continued to scale strongly with SPI frequency.
- Embassy tasks continued executing during DMA transfers but not during blocking transfers.
- Cortex-M DWT cycle measurements closely matched expected elapsed core-clock cycles.
- Repeated hardware experiments are analyzed independently from the representative single-run results.
- Statistical analysis reports mean throughput, sample standard deviation, and a 95% confidence interval for every benchmark configuration.

The performance values in the tables above are representative single-run
hardware measurements. Repeated experiment results are stored separately and
used for statistical analysis.

---

## Hardware

| Component | Configuration |
|:----------|:--------------|
| Board | MM6108-EKH05 |
| MCU | STM32U585AI |
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

## What the Benchmark Measures

The framework measures:

- transfer latency
- aggregate transfer time
- minimum and maximum transfer time
- throughput
- repeated-transfer performance
- performance across different payload sizes
- performance across different SPI frequencies
- elapsed Cortex-M core cycles
- average elapsed cycles per transfer
- application task concurrency during DMA
- blocking vs DMA performance
- automatic DMA crossover detection
- repeated-run mean throughput
- sample standard deviation
- 95% confidence intervals

The benchmark currently tests:

```text
SPI clocks:
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

Iterations per configuration:
100
```

A complete hardware run produces:

```text
4 SPI frequencies
×
9 payload sizes
×
2 transfer methods
=
72 benchmark measurements
```

For repeated statistical analysis, the complete benchmark is executed
independently 30 times:

```text
30 independent runs
×
72 measurements per run
=
2,160 measurements
```

---

## Performance Results

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

These results demonstrate that DMA is not automatically faster than blocking
SPI. Transfer size and bus frequency determine whether the DMA setup and
synchronization overhead is worthwhile.

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

At 4 MHz and 8 MHz, the graphs clearly show the point where DMA begins
outperforming blocking SPI.

---

## DMA Crossover Analysis

Intermediate payload sizes were added specifically to identify the transition
between blocking and DMA performance.

| SPI Clock | Measured Crossover |
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

The framework reports an interval rather than an exact byte-level crossover
because only configured payload sizes are measured.

---

## Cortex-M DWT Cycle Measurement

The benchmark uses the Cortex-M **Data Watchpoint and Trace (DWT)** hardware
cycle counter alongside microsecond timing.

For each benchmark it records:

- total elapsed core cycles
- average elapsed core cycles per transfer

### 256-Byte Results

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

At 8 MHz, the 256-byte DMA benchmark transferred 25,600 bytes in approximately:

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

The DWT measurement represents **elapsed processor clock cycles** between the
beginning and end of the benchmark.

For asynchronous DMA transfers, this includes periods where the benchmark task
is suspended while waiting for DMA completion.

Therefore, the value should not be interpreted as CPU utilization or as the
number of CPU instructions executed by the DMA operation.

---

## DMA Concurrency

A background Embassy task increments a counter approximately once per
millisecond while benchmark operations execute.

```rust
#[embassy_executor::task]
async fn cpu_activity_task() {
    loop {
        CPU_ACTIVITY.fetch_add(1, Ordering::Relaxed);
        Timer::after_millis(1).await;
    }
}
```

Measured task progress:

| SPI Clock | Blocking | DMA |
|----------:|---------:|----:|
| 1 MHz | 0 | 854 |
| 2 MHz | 0 | 454 |
| 4 MHz | 0 | 257 |
| 8 MHz | 0 | 178 |

The background task made no progress while blocking transfers were active.

During DMA transfers, the scheduler continued running other application work.

This is evidence of concurrency, not a CPU utilization percentage.

---

## Architecture

The benchmark separates hardware-specific SPI code from benchmark logic using
small transfer interfaces.

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

This allows the benchmark engine to operate independently of the underlying SPI
implementation.

### Project Structure

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
    ├── benchmark_runs.csv
    ├── benchmark_table.txt
    ├── throughput_statistics.csv
    ├── runs
    │   ├── benchmark_run_001.csv
    │   ├── benchmark_run_002.csv
    │   └── ...
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

### Main Components

`spi.rs`

- SPI1 configuration
- blocking transfers
- DMA-backed asynchronous transfers
- software chip select
- runtime SPI frequency control

`benchmark.rs`

- repeated benchmark execution
- timing statistics
- throughput calculation
- DWT cycle collection

`cycle_counter.rs`

- Cortex-M DWT initialization
- hardware cycle-counter access

`transfer.rs`

- hardware-independent transfer interfaces

`tools/capture_csv.py`

- launches one complete hardware benchmark
- captures RTT output
- parses benchmark measurements
- exports the latest run to CSV
- generates readable tables
- generates benchmark graphs

`tools/run_experiments.py`

- runs complete hardware benchmark experiments repeatedly
- accepts the number of independent runs from the command line
- preserves each completed run as a sequentially numbered CSV file
- automatically selects the next available run number
- prevents previous experiment runs from being overwritten
- appends every completed run to a combined dataset with a `run_id`

`tools/analyze_results.py`

- loads the combined repeated-run dataset
- validates required benchmark fields
- verifies that every run contains 72 measurements
- groups measurements by SPI frequency, transfer method, and payload size
- calculates mean throughput for each benchmark configuration
- calculates sample standard deviation using the repeated hardware measurements
- calculates a two-sided 95% confidence interval using Student's t distribution
- exports statistical results to `results/throughput_statistics.csv`

---

## Benchmark Data

Complete single-run measurements are available directly in the repository:

- [Raw CSV](results/benchmark.csv)
- [Formatted Benchmark Table](results/benchmark_table.txt)

The single-run CSV contains:

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

The latest single benchmark run is stored in:

```text
results/benchmark.csv
```

### Repeated Research Dataset

Independent experiment runs are preserved under:

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

All repeated-run measurements are also collected in:

```text
results/benchmark_runs.csv
```

The combined dataset includes a `run_id` column:

```text
run_id,spi_frequency_hz,method,payload_bytes,...
1,1000000,blocking,4,...
1,1000000,dma,4,...
2,1000000,blocking,4,...
```

The repeated research dataset contains:

```text
30 independent runs
×
72 configurations
=
2,160 benchmark measurements
```

### Throughput Statistics

Statistical throughput results are exported to:

```text
results/throughput_statistics.csv
```

The file contains one row for each of the 72 benchmark configurations.

Each row contains:

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

Statistics are calculated independently for every combination of:

```text
SPI frequency
+
transfer method
+
payload size
```

For the repeated experiments:

```text
sample count = 30
```

The standard deviation is the **sample standard deviation**.

The 95% confidence interval is calculated using:

```text
mean ± t * (s / sqrt(n))
```

where:

```text
mean = sample mean throughput
s    = sample standard deviation
n    = number of independent runs
t    = Student's t critical value
```

For 30 runs:

```text
n = 30
degrees of freedom = 29
```

This provides both the average measured performance and an estimate of the
uncertainty in that average.

---

## Generate Results

Install Matplotlib and SciPy:

```bash
sudo apt install python3-matplotlib python3-scipy
```

### Single Benchmark Run

Run:

```bash
python3 tools/capture_csv.py
```

The script runs the firmware through `cargo run`, captures RTT output, and
automatically regenerates:

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

### Repeated Experiment Runs

Multiple independent hardware benchmark runs can be collected using:

```bash
python3 tools/run_experiments.py 30
```

The argument specifies how many complete benchmark runs to execute.

Each run executes all 72 benchmark measurement configurations.

Completed runs are preserved separately:

```text
results/runs/benchmark_run_001.csv
results/runs/benchmark_run_002.csv
results/runs/benchmark_run_003.csv
...
```

The next available run number is selected automatically, so existing experiment
files are not overwritten.

Each completed run is also appended to:

```text
results/benchmark_runs.csv
```

The combined dataset adds a `run_id` column so measurements from independent
hardware runs remain distinguishable.

`results/benchmark.csv` continues to contain the most recent single benchmark
run generated by `capture_csv.py`.

### Statistical Analysis

Run:

```bash
python3 tools/analyze_results.py
```

The analysis utility performs:

```text
results/benchmark_runs.csv
        ↓
validate required fields
        ↓
verify 72 measurements per run
        ↓
group matching benchmark configurations
        ↓
calculate mean throughput
        ↓
calculate sample standard deviation
        ↓
calculate standard error
        ↓
calculate 95% Student's t confidence interval
        ↓
results/throughput_statistics.csv
```

For the 30-run dataset, a successful analysis reports:

```text
Loaded 2160 benchmark measurements from 30 independent runs.
Validated 30 runs with 72 measurements each.
```

The resulting statistics file contains:

```text
1 header
+
72 benchmark configurations
=
73 lines
```

Verify with:

```bash
wc -l results/throughput_statistics.csv
```

Expected:

```text
73 results/throughput_statistics.csv
```

---

## Statistical Method

For a benchmark configuration with throughput measurements:

```text
x1, x2, x3, ..., xn
```

the arithmetic mean is:

```text
x̄ = (x1 + x2 + ... + xn) / n
```

The sample standard deviation is calculated using:

```text
s = sqrt(Σ(xi - x̄)^2 / (n - 1))
```

The standard error of the mean is:

```text
SE = s / sqrt(n)
```

The two-sided 95% confidence interval is:

```text
x̄ ± t(0.975, n - 1) × SE
```

Student's t distribution is used instead of assuming a fixed normal critical
value because the mean and variability are estimated from a finite number of
independent hardware runs.

These statistics describe repeated measurements of the implemented benchmark.
They should not be interpreted as guarantees for every STM32U585 application or
every SPI peripheral configuration.

---

## Build

Install the embedded Rust target:

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

Connect the MM6108-EKH05 using ST-LINK.

Run:

```bash
cargo run
```

`probe-rs` flashes the STM32U585 and RTT output is displayed using `defmt`.

Example representative result:

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

An optimized firmware image can be created with:

```bash
cargo build --release
```

The ELF executable is generated under:

```text
target/thumbv8m.main-none-eabihf/release/
```

Release artifacts can include:

```text
spi-benchmark.elf
spi-benchmark.bin
spi-benchmark.hex
benchmark.csv
```

The ELF file preserves debugging information, while BIN and HEX files can be
used for direct firmware flashing.

---

## Technologies

- Rust
- Embedded Rust
- Embassy
- STM32U585
- ARM Cortex-M33
- SPI
- DMA
- DWT cycle counter
- asynchronous embedded programming
- probe-rs
- ST-LINK
- defmt / RTT
- Python
- Python CSV processing
- Python statistics
- SciPy
- Matplotlib
- Git / GitHub

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
transfer statistics
DMA SPI
DMA benchmarking
DMA concurrency testing
automatic blocking/DMA comparison
SPI clock scaling
DMA crossover analysis
DWT core-cycle measurement
CSV export
benchmark visualization
repeated experiment capture
combined repeated-run dataset
dataset validation
mean throughput analysis
sample standard deviation analysis
95% confidence interval analysis
```

Each major feature was built and tested on the STM32U585 before being merged
into `main`.

---

## Why This Project

This project explores an important embedded-systems engineering question:

> When does the additional complexity of DMA actually provide a measurable
> performance advantage over a simple blocking peripheral transfer?

Rather than assuming DMA is always faster, the benchmark measures the trade-off
experimentally across different transfer sizes and SPI frequencies.

The repeated-run dataset extends the benchmark beyond a single hardware
measurement by collecting independent experiments and measuring both average
performance and run-to-run variability.

Mean throughput describes the central measured performance, sample standard
deviation describes variation between repeated runs, and the 95% confidence
interval quantifies uncertainty in the estimated mean.

The results show that the blocking-to-DMA trade-off depends strongly on payload
size, peripheral frequency, software overhead, and the ability to overlap
communication with other application work.