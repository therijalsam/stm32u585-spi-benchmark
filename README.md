# STM32U585 SPI Benchmark

An embedded Rust project for measuring and comparing SPI transfer performance on an STM32U585.

I'm developing and testing this on the MM6108-EKH05 board using Embassy and probe-rs.

The project benchmarks blocking and DMA-backed SPI transfers across different
payload sizes and SPI clock frequencies. It measures transfer timing,
throughput, timing variation, elapsed core cycles, task concurrency, and the
payload region where DMA begins to outperform blocking SPI.

## Goal

The goal of this project is to build a reusable SPI performance benchmarking
framework for the STM32U585 and use it to understand how different SPI transfer
methods behave in a real embedded system.

The benchmark focuses on:

- transfer latency
- throughput
- repeated-transfer performance
- performance across different payload sizes
- performance across different SPI clock frequencies
- elapsed Cortex-M core cycles
- application task concurrency during DMA transfers
- the crossover between blocking and DMA performance

The purpose is not only to make SPI communication work, but to understand the
performance trade-offs between blocking and DMA-backed communication and
determine when each method is more appropriate.

## Hardware

- MM6108-EKH05
- STM32U585AI
- ST-LINK V3

### SPI1 Pins

| Signal | Pin |
| ------ | --- |
| SCK | PE13 |
| MISO | PE14 |
| MOSI | PE15 |
| CS | PE12 |

Chip select is controlled in software using PE12.

## Clock Configuration

The STM32U585 is configured to use its internal 16 MHz HSI clock as the system
clock for the benchmark.

With the current configuration, SPI1 supports benchmark frequencies up to
8 MHz.

The firmware changes the SPI frequency at runtime and currently tests:

- 1 MHz
- 2 MHz
- 4 MHz
- 8 MHz

Before each benchmark, the firmware reports both the requested SPI frequency
and the actual configured frequency.

## Current Features

- STM32U585 firmware written in Rust
- Embassy-based hardware initialization
- SPI1 initialization
- Blocking SPI writes
- DMA-backed asynchronous SPI writes
- Software-controlled chip select
- Blocking `SpiTransfer` interface
- DMA `DmaTransfer` interface
- Benchmark timer
- Cortex-M DWT hardware cycle counter
- Repeated SPI benchmarking
- Multiple SPI payload sizes
- Transfer timing
- Total elapsed core-cycle measurement
- Average core cycles per transfer
- Minimum and maximum per-transfer timing
- Throughput calculation
- CPU task concurrency during DMA transfers
- Automatic blocking vs DMA throughput comparison
- Runtime SPI clock configuration
- SPI benchmarking at 1, 2, 4, and 8 MHz
- Blocking vs DMA comparison across SPI clock frequencies
- Intermediate payload benchmarking around the DMA crossover region
- Automatic blocking-to-DMA crossover detection

## Project Structure

```text
.
├── Cargo.toml
├── build.rs
├── memory.x
└── src
    ├── main.rs
    ├── benchmark.rs
    ├── cycle_counter.rs
    ├── spi.rs
    ├── timer.rs
    └── transfer.rs
```

### `main.rs`

Initializes the STM32U585 using the internal HSI clock, enables the Cortex-M DWT
cycle counter, creates the SPI driver, runs blocking and DMA benchmarks across
multiple SPI clock frequencies and payload sizes, measures background task
progress, automatically compares both transfer methods, and detects the measured
blocking-to-DMA crossover interval.

### `spi.rs`

Contains the SPI1 implementation, software chip-select handling, blocking and
DMA-backed transfers, and runtime SPI clock configuration.

The SPI driver supports:

- blocking SPI writes
- DMA-backed asynchronous SPI writes
- software-controlled chip select
- runtime SPI frequency changes

### `transfer.rs`

Defines the interfaces used by the benchmark framework.

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

This keeps the benchmark logic separate from the hardware-specific SPI
implementation.

### `timer.rs`

Contains the timer used to measure SPI transfer duration.

### `cycle_counter.rs`

Provides access to the Cortex-M DWT hardware cycle counter.

The DWT counter is initialized once during firmware startup and provides a
hardware counter that increments with the processor core clock.

The benchmark uses the counter to measure:

- total elapsed core cycles
- average elapsed core cycles per transfer

### `benchmark.rs`

Contains the benchmark configuration and execution logic for both blocking and
DMA transfers.

It calculates:

- benchmark iterations
- bytes transferred
- total elapsed time
- total elapsed core cycles
- aggregate average transfer time
- average core cycles per transfer
- minimum transfer time
- maximum transfer time
- throughput

## Current Benchmark

The benchmark currently tests nine payload sizes.

| Payload Size | Iterations | Total Bytes |
|-------------:|-----------:|------------:|
| 4 bytes | 100 | 400 bytes |
| 16 bytes | 100 | 1,600 bytes |
| 24 bytes | 100 | 2,400 bytes |
| 32 bytes | 100 | 3,200 bytes |
| 40 bytes | 100 | 4,000 bytes |
| 48 bytes | 100 | 4,800 bytes |
| 56 bytes | 100 | 5,600 bytes |
| 64 bytes | 100 | 6,400 bytes |
| 256 bytes | 100 | 25,600 bytes |

The payload sizes are configured in one place:

```rust
const PAYLOAD_SIZES: [usize; 9] = [4, 16, 24, 32, 40, 48, 56, 64, 256];
```

A single 256-byte test buffer is sliced according to the requested payload
size.

The same payload sizes and iteration count are used for blocking and DMA
transfers at every SPI clock frequency.

## SPI Clock Scaling Results

The following tables summarize representative payload sizes from the latest
benchmark run.

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
| 8 MHz | 85,269 B/s | 221,208 B/s | 595,792 B/s | 853,390 B/s |

## Blocking vs DMA

The firmware automatically compares blocking and DMA throughput after every
clock-frequency benchmark.

| SPI Clock | 4 B | 16 B | 64 B | 256 B |
|----------:|:----|:-----|:-----|:------|
| 1 MHz | Blocking +25% | Blocking +8% | Blocking +2% | Blocking +1% |
| 2 MHz | Blocking +46% | Blocking +17% | Blocking +4% | Blocking +2% |
| 4 MHz | Blocking +81% | Blocking +7% | DMA +48% | DMA +64% |
| 8 MHz | Blocking +89% | Blocking +9% | DMA +115% | DMA +197% |

The results show that DMA is not automatically faster than blocking SPI.

At 1 MHz and 2 MHz, blocking SPI provides higher throughput for every payload
size tested.

At 4 MHz and 8 MHz, blocking remains faster for the smallest transfers, while
DMA becomes significantly faster once the payload becomes large enough.

At 8 MHz, the 256-byte DMA benchmark reaches:

```text
853,390 bytes/s
```

while blocking SPI reaches:

```text
287,211 bytes/s
```

The firmware reports DMA as approximately 197% faster for this test.

## DMA Crossover Analysis

The benchmark includes intermediate payload sizes between 16 and 64 bytes to
identify more precisely where DMA begins to outperform blocking SPI.

After each clock-frequency benchmark, the firmware searches for a transition
where blocking SPI was faster at one tested payload size and DMA became faster
at the next tested payload size.

The latest hardware run produced:

| SPI Clock | Crossover Result |
|----------:|:-----------------|
| 1 MHz | No crossover detected |
| 2 MHz | No crossover detected |
| 4 MHz | Between 16 and 24 bytes |
| 8 MHz | Between 16 and 24 bytes |

At 1 MHz and 2 MHz, blocking SPI remained faster throughout the complete tested
range from 4 to 256 bytes.

At 4 MHz:

| Payload | Blocking | DMA | Faster |
|--------:|---------:|----:|:-------|
| 16 B | 237,706 B/s | 221,514 B/s | Blocking |
| 24 B | 253,137 B/s | 306,239 B/s | DMA |
| 32 B | 261,630 B/s | 344,123 B/s | DMA |
| 40 B | 267,165 B/s | 368,765 B/s | DMA |
| 48 B | 270,849 B/s | 372,902 B/s | DMA |
| 56 B | 273,424 B/s | 395,619 B/s | DMA |
| 64 B | 275,482 B/s | 408,919 B/s | DMA |

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

The measured transition therefore occurs somewhere between 16 and 24 bytes at
both 4 MHz and 8 MHz.

The benchmark reports an interval rather than claiming an exact byte-level
crossover because only the configured payload sizes are measured.

## Core Cycle Measurement

The benchmark uses the Cortex-M DWT hardware cycle counter in addition to the
existing microsecond timer.

For each blocking and DMA benchmark, the firmware records:

- total elapsed core cycles
- average elapsed core cycles per transfer

The STM32U585 is configured to run from the 16 MHz HSI clock, so approximately
16 core cycles should elapse for every microsecond of wall-clock time.

The measurements closely follow that relationship.

### 256-Byte Cycle Results

| SPI Clock | Blocking Total Cycles | Blocking Cycles / Transfer | DMA Total Cycles | DMA Cycles / Transfer |
|----------:|----------------------:|---------------------------:|-----------------:|----------------------:|
| 1 MHz | 3,305,697 | 33,056 | 3,353,281 | 33,532 |
| 2 MHz | 1,664,301 | 16,643 | 1,707,302 | 17,073 |
| 4 MHz | 1,428,085 | 14,280 | 867,283 | 8,672 |
| 8 MHz | 1,426,181 | 14,261 | 480,019 | 4,800 |

The blocking 256-byte benchmark improves significantly when increasing the SPI
clock from 1 MHz to 4 MHz, but its elapsed core-cycle count changes very little
between 4 MHz and 8 MHz.

This matches the throughput measurements, where blocking throughput also levels
off at higher SPI clock frequencies.

DMA shows a different pattern.

For the 256-byte DMA transfer, the average elapsed cycle count decreases from:

```text
33,532 cycles per transfer at 1 MHz
```

to:

```text
4,800 cycles per transfer at 8 MHz
```

The 8 MHz DMA benchmark transferred 25,600 bytes in:

```text
29,998 us
```

and measured:

```text
480,019 elapsed core cycles
```

At a 16 MHz core clock, 29,998 microseconds corresponds to approximately:

```text
479,968 cycles
```

which closely matches the DWT measurement.

### Important Interpretation

The DWT value measures elapsed processor clock cycles between the beginning and
end of the benchmark.

For blocking SPI, this interval covers the period during which the blocking
benchmark keeps control of the processor.

For DMA-backed asynchronous SPI, the measurement also includes periods where
the benchmark task is suspended while waiting for DMA completion.

Therefore, the DMA cycle value represents elapsed core-clock cycles across the
asynchronous operation.

It does not represent CPU utilization and should not be interpreted as the
number of cycles actively spent executing DMA-related instructions.

## Clock Scaling Analysis

The blocking implementation initially benefits from increasing SPI frequency,
but its throughput begins to level off at higher bus speeds.

For the 256-byte blocking benchmark:

| SPI Clock | Throughput |
|----------:|-----------:|
| 1 MHz | 123,909 B/s |
| 2 MHz | 246,118 B/s |
| 4 MHz | 286,828 B/s |
| 8 MHz | 287,211 B/s |

Increasing the SPI clock from 4 MHz to 8 MHz produces almost no additional
blocking throughput.

The cycle measurements show the same behavior:

| SPI Clock | Blocking Cycles / 256-Byte Transfer |
|----------:|-------------------------------------:|
| 1 MHz | 33,056 |
| 2 MHz | 16,643 |
| 4 MHz | 14,280 |
| 8 MHz | 14,261 |

DMA behaves differently:

| SPI Clock | 256-byte DMA Throughput | DMA Cycles / Transfer |
|----------:|-------------------------:|----------------------:|
| 1 MHz | 122,150 B/s | 33,532 |
| 2 MHz | 239,918 B/s | 17,073 |
| 4 MHz | 472,307 B/s | 8,672 |
| 8 MHz | 853,390 B/s | 4,800 |

DMA continues to scale much more strongly with SPI frequency for larger
transfers.

The throughput and elapsed-cycle measurements both show that blocking
performance begins to plateau at higher SPI frequencies, while DMA continues to
benefit from increasing SPI bus speed.

## CPU Concurrency Test

The firmware checks whether another application task can make progress while
SPI communication is active.

A background Embassy task increments a counter approximately once every
millisecond.

```rust
#[embassy_executor::task]
async fn cpu_activity_task() {
    loop {
        CPU_ACTIVITY.fetch_add(1, Ordering::Relaxed);

        Timer::after_millis(1).await;
    }
}
```

The latest benchmark run produced:

| SPI Clock | Blocking Task Progress | DMA Task Progress |
|----------:|-----------------------:|------------------:|
| 1 MHz | 0 | 854 |
| 2 MHz | 0 | 454 |
| 4 MHz | 0 | 257 |
| 8 MHz | 0 | 178 |

The background task made no progress during any blocking benchmark.

During every DMA benchmark, the background task continued to execute while SPI
communication was active.

The DMA task-progress count becomes smaller at higher SPI frequencies because
the complete DMA benchmark finishes more quickly.

This counter is not a CPU utilization percentage. It only shows whether another
Embassy task was able to execute while SPI communication was in progress.

## Timing Method

Aggregate timing is measured using one timer around the complete set of repeated
SPI transfers.

```text
start timer

transfer
transfer
transfer
...
100 transfers

stop timer
```

The aggregate average is calculated using:

```text
aggregate_average = total_elapsed_time / iterations
```

The DWT cycle counter is measured across the same repeated-transfer benchmark.

```text
start cycle counter measurement

transfer
transfer
transfer
...
100 transfers

read cycle counter
```

Average cycles per transfer are calculated using:

```text
average_cycles = total_elapsed_cycles / iterations
```

Minimum and maximum transfer times are measured separately by timing individual
transfers.

Because individual timing adds measurement overhead, the measured minimum can
sometimes be slightly higher than the aggregate average.

## Throughput

Throughput is calculated from the total number of transferred bytes and total
elapsed time.

```text
throughput = total_bytes × 1,000,000 / elapsed_time_us
```

For example, the 8 MHz 256-byte DMA benchmark transferred:

```text
25,600 bytes
```

in:

```text
29,998 us
```

which gives approximately:

```text
853,390 bytes/s
```

The same benchmark measured:

```text
480,019 elapsed core cycles
```

or approximately:

```text
4,800 core cycles per transfer
```

## Build

Install the Rust target:

```bash
rustup target add thumbv8m.main-none-eabihf
```

Build the firmware:

```bash
cargo build
```

Format the project:

```bash
cargo fmt
```

## Flash and Run

Connect the board using ST-LINK and run:

```bash
cargo run
```

The project uses probe-rs to flash the STM32U585.

Benchmark output is displayed through RTT using `defmt`.

Example:

```text
STM32U585 SPI Benchmark
Firmware started
DWT cycle counter enabled
SPI1 maximum frequency: 8000000 Hz

Requested SPI frequency: 8000000 Hz
Actual SPI frequency: 8000000 Hz

Starting blocking SPI benchmarks
SPI frequency: 8000000 Hz

Payload size: 256 bytes
Iterations: 100
Total elapsed time: 89133 us
Total elapsed core cycles: 1426181
Average core cycles per transfer: 14261
Throughput: 287211 bytes/s

Starting DMA SPI benchmarks
SPI frequency: 8000000 Hz

DMA payload size: 256 bytes
Iterations: 100
Total elapsed time: 29998 us
Total elapsed core cycles: 480019
Average core cycles per transfer: 4800
DMA throughput: 853390 bytes/s

CPU worker progress during DMA: 178

Blocking vs DMA comparison
SPI frequency: 8000000 Hz

Comparison for 256 byte payload
Blocking throughput: 287211 bytes/s
DMA throughput: 853390 bytes/s
Faster method: DMA
DMA throughput improvement: 197%

DMA crossover analysis at 8000000 Hz
DMA crossover detected between 16 and 24 bytes

SPI clock benchmarks complete
Benchmark complete
```

## Development

The project is developed using feature branches.

Each feature is built and tested on the STM32U585 before being merged into
`main`.

Some of the completed branches include:

```text
feature/benchmark-timer
feature/spi-initialization
feature/blocking-spi-write
feature/spi-transfer-interface
feature/blocking-benchmark
feature/transfer-timing
feature/throughput-calculation
feature/repeated-benchmark
feature/benchmark-config
feature/multiple-transfer-sizes
feature/transfer-statistics
feature/dma-spi
feature/dma-benchmark
feature/dma-cpu-concurrency
feature/automatic-comparison
feature/spi-clock-benchmark
feature/crossover-analysis
feature/cpu-cycle-measurement
```

The README is updated whenever a feature changes the behavior, measurements, or
capabilities of the firmware so that it reflects the current state of the
project.