# STM32U585 SPI Benchmark

An embedded Rust project for measuring and comparing SPI transfer performance on an STM32U585.

I'm developing and testing this on the MM6108-EKH05 board using Embassy and probe-rs.

The project benchmarks blocking and DMA-backed SPI transfers across different
payload sizes and SPI clock frequencies. It measures transfer timing,
throughput, timing variation, task concurrency, and the payload region where
DMA begins to outperform blocking SPI.

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
- Repeated SPI benchmarking
- Multiple SPI payload sizes
- Transfer timing
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
    ├── spi.rs
    ├── timer.rs
    └── transfer.rs
```

### `main.rs`

Initializes the STM32U585 using the internal HSI clock, creates the SPI driver,
runs blocking and DMA benchmarks across multiple SPI clock frequencies and
payload sizes, measures background task progress, automatically compares both
transfer methods, and detects the measured blocking-to-DMA crossover interval.

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

### `benchmark.rs`

Contains the benchmark configuration and execution logic for both blocking and
DMA transfers.

It calculates:

- benchmark iterations
- bytes transferred
- total elapsed time
- aggregate average transfer time
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
const PAYLOAD_SIZES: [usize; 9] = [
    4,
    16,
    24,
    32,
    40,
    48,
    56,
    64,
    256,
];
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
| 1 MHz | 79,856 B/s | 109,656 B/s | 120,690 B/s | 123,909 B/s |
| 2 MHz | 124,649 B/s | 199,775 B/s | 235,216 B/s | 246,118 B/s |
| 4 MHz | 154,023 B/s | 238,024 B/s | 275,600 B/s | 286,828 B/s |
| 8 MHz | 161,420 B/s | 242,314 B/s | 276,900 B/s | 287,211 B/s |

### DMA Throughput

| SPI Clock | 4 B | 16 B | 64 B | 256 B |
|----------:|----:|-----:|-----:|------:|
| 1 MHz | 63,653 B/s | 100,882 B/s | 117,950 B/s | 122,136 B/s |
| 2 MHz | 85,142 B/s | 169,186 B/s | 224,474 B/s | 239,918 B/s |
| 4 MHz | 85,124 B/s | 221,330 B/s | 409,024 B/s | 472,089 B/s |
| 8 MHz | 85,142 B/s | 221,330 B/s | 595,404 B/s | 853,390 B/s |

## Blocking vs DMA

The firmware automatically compares blocking and DMA throughput after every
clock-frequency benchmark.

| SPI Clock | 4 B | 16 B | 64 B | 256 B |
|----------:|:----|:-----|:-----|:------|
| 1 MHz | Blocking +25% | Blocking +8% | Blocking +2% | Blocking +1% |
| 2 MHz | Blocking +46% | Blocking +18% | Blocking +4% | Blocking +2% |
| 4 MHz | Blocking +80% | Blocking +7% | DMA +48% | DMA +64% |
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
| 16 B | 238,024 B/s | 221,330 B/s | Blocking |
| 24 B | 253,378 B/s | 305,304 B/s | DMA |
| 32 B | 261,608 B/s | 344,012 B/s | DMA |
| 40 B | 267,004 B/s | 368,527 B/s | DMA |
| 48 B | 270,697 B/s | 372,757 B/s | DMA |
| 56 B | 273,397 B/s | 393,783 B/s | DMA |
| 64 B | 275,600 B/s | 409,024 B/s | DMA |

At 8 MHz:

| Payload | Blocking | DMA | Faster |
|--------:|---------:|----:|:-------|
| 16 B | 242,314 B/s | 221,330 B/s | Blocking |
| 24 B | 256,602 B/s | 330,169 B/s | DMA |
| 32 B | 264,178 B/s | 413,810 B/s | DMA |
| 40 B | 269,305 B/s | 473,709 B/s | DMA |
| 48 B | 272,665 B/s | 524,762 B/s | DMA |
| 56 B | 275,008 B/s | 561,403 B/s | DMA |
| 64 B | 276,900 B/s | 595,404 B/s | DMA |

The measured transition therefore occurs somewhere between 16 and 24 bytes at
both 4 MHz and 8 MHz.

The benchmark reports an interval rather than claiming an exact byte-level
crossover because only the configured payload sizes are measured.

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

DMA behaves differently:

| SPI Clock | 256-byte DMA Throughput |
|----------:|-------------------------:|
| 1 MHz | 122,136 B/s |
| 2 MHz | 239,918 B/s |
| 4 MHz | 472,089 B/s |
| 8 MHz | 853,390 B/s |

DMA continues to scale much more strongly with SPI frequency for larger
transfers.

These measurements indicate that software and CPU overhead increasingly limit
the blocking implementation as SPI bus speed increases, while DMA is better
able to take advantage of the higher transfer rate.

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
| 1 MHz | 0 | 857 |
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
SPI1 maximum frequency: 8000000 Hz

Requested SPI frequency: 8000000 Hz
Actual SPI frequency: 8000000 Hz

Starting blocking SPI benchmarks
SPI frequency: 8000000 Hz

Payload size: 16 bytes
Throughput: 242314 bytes/s

Payload size: 24 bytes
Throughput: 256602 bytes/s

Starting DMA SPI benchmarks
SPI frequency: 8000000 Hz

DMA payload size: 16 bytes
DMA throughput: 221330 bytes/s

DMA payload size: 24 bytes
DMA throughput: 330169 bytes/s

Blocking vs DMA comparison

Comparison for 16 byte payload
Faster method: Blocking

Comparison for 24 byte payload
Faster method: DMA

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
```

The README is updated whenever a feature changes the behavior, measurements, or
capabilities of the firmware so that it reflects the current state of the
project.