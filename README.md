# STM32U585 SPI Benchmark

An embedded Rust project for measuring and comparing SPI transfer performance on an STM32U585.

I'm developing and testing this on the MM6108-EKH05 board using Embassy and probe-rs.

The project benchmarks blocking and DMA-backed SPI transfers across different
payload sizes and SPI clock frequencies. It measures transfer timing,
throughput, timing variation, and whether other application tasks can continue
executing while SPI communication is active.

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
runs blocking and DMA benchmarks across multiple SPI clock frequencies,
measures background task progress, and automatically compares the performance
of both transfer methods.

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

The benchmark tests four payload sizes:

| Payload Size | Iterations | Total Bytes |
|-------------:|-----------:|------------:|
| 4 bytes | 100 | 400 bytes |
| 16 bytes | 100 | 1,600 bytes |
| 64 bytes | 100 | 6,400 bytes |
| 256 bytes | 100 | 25,600 bytes |

Each test buffer contains repeated `0xAA` values:

```rust
let data_4 = [0xAA; 4];
let data_16 = [0xAA; 16];
let data_64 = [0xAA; 64];
let data_256 = [0xAA; 256];
```

The same payload sizes and iteration count are used for blocking and DMA
transfers at every SPI clock frequency.

## SPI Clock Scaling Results

### Blocking Throughput

| SPI Clock | 4 B | 16 B | 64 B | 256 B |
|----------:|----:|-----:|-----:|------:|
| 1 MHz | 79,856 B/s | 109,589 B/s | 120,690 B/s | 123,909 B/s |
| 2 MHz | 124,649 B/s | 199,625 B/s | 235,216 B/s | 246,115 B/s |
| 4 MHz | 154,023 B/s | 238,024 B/s | 275,493 B/s | 286,857 B/s |
| 8 MHz | 161,420 B/s | 242,314 B/s | 276,900 B/s | 287,208 B/s |

### DMA Throughput

| SPI Clock | 4 B | 16 B | 64 B | 256 B |
|----------:|----:|-----:|-----:|------:|
| 1 MHz | 63,714 B/s | 100,844 B/s | 117,965 B/s | 122,158 B/s |
| 2 MHz | 85,251 B/s | 168,883 B/s | 224,403 B/s | 239,693 B/s |
| 4 MHz | 85,251 B/s | 218,132 B/s | 407,280 B/s | 472,124 B/s |
| 8 MHz | 85,251 B/s | 218,132 B/s | 587,533 B/s | 850,809 B/s |

## Blocking vs DMA

The firmware automatically compares blocking and DMA throughput after each
clock-frequency benchmark.

| SPI Clock | 4 B | 16 B | 64 B | 256 B |
|----------:|:----|:-----|:-----|:------|
| 1 MHz | Blocking +25% | Blocking +8% | Blocking +2% | Blocking +1% |
| 2 MHz | Blocking +46% | Blocking +18% | Blocking +4% | Blocking +2% |
| 4 MHz | Blocking +80% | Blocking +9% | DMA +47% | DMA +64% |
| 8 MHz | Blocking +89% | Blocking +11% | DMA +112% | DMA +196% |

The results show that DMA is not automatically faster than blocking SPI.

At 1 MHz and 2 MHz, blocking SPI provides slightly higher throughput for all
payload sizes tested.

At 4 MHz and 8 MHz, blocking remains faster for the small 4-byte and 16-byte
transfers, while DMA becomes significantly faster for the larger 64-byte and
256-byte transfers.

At 8 MHz, the 256-byte DMA benchmark reaches:

```text
850,809 bytes/s
```

while the blocking implementation reaches:

```text
287,208 bytes/s
```

The firmware reports DMA as approximately 196% faster for this test.

For the 4 MHz and 8 MHz tests, the transition between blocking and DMA
performance occurs somewhere between the 16-byte and 64-byte payload sizes.

## Clock Scaling Analysis

The blocking implementation improves when moving from 1 MHz to higher SPI
frequencies, but its throughput begins to level off.

For example, the 256-byte blocking benchmark produces:

| SPI Clock | Throughput |
|----------:|-----------:|
| 1 MHz | 123,909 B/s |
| 2 MHz | 246,115 B/s |
| 4 MHz | 286,857 B/s |
| 8 MHz | 287,208 B/s |

Increasing the SPI clock from 4 MHz to 8 MHz produces almost no additional
blocking throughput for this payload.

DMA behaves differently:

| SPI Clock | 256-byte DMA Throughput |
|----------:|-------------------------:|
| 1 MHz | 122,158 B/s |
| 2 MHz | 239,693 B/s |
| 4 MHz | 472,124 B/s |
| 8 MHz | 850,809 B/s |

DMA continues to scale much more strongly with SPI frequency for larger
transfers.

The measurements suggest that software and CPU overhead increasingly limit the
blocking implementation as SPI bus speed increases, while DMA is better able to
take advantage of the higher transfer rate.

## CPU Concurrency Test

The firmware also checks whether another application task can make progress
while SPI communication is active.

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

The measured task progress across the clock-scaling benchmark was:

| SPI Clock | Blocking Task Progress | DMA Task Progress |
|----------:|-----------------------:|------------------:|
| 1 MHz | 0 | 525 |
| 2 MHz | 0 | 273 |
| 4 MHz | 0 | 148 |
| 8 MHz | 0 | 94 |

The background task made no progress during any blocking benchmark.

During every DMA benchmark, the background task continued to execute while SPI
communication was active.

The DMA task-progress count becomes smaller at higher SPI frequencies because
the entire DMA benchmark finishes faster.

This counter is not a CPU utilization percentage. It only shows whether another
Embassy task was able to execute while SPI communication was in progress.

## Timing Method

Aggregate timing is measured using one timer around the complete set of
repeated SPI transfers.

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
30,089 us
```

which gives approximately:

```text
850,809 bytes/s
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
Maximum supported SPI frequency: 8000000 Hz
Actual SPI frequency: 8000000 Hz

Starting blocking SPI benchmarks
SPI frequency: 8000000 Hz

Payload size: 256 bytes
Iterations: 100
Throughput: 287208 bytes/s

Starting DMA SPI benchmarks
SPI frequency: 8000000 Hz

DMA payload size: 256 bytes
Iterations: 100
DMA throughput: 850809 bytes/s

CPU worker progress during DMA: 94

Blocking vs DMA comparison
SPI frequency: 8000000 Hz

Comparison for 256 byte payload
Blocking throughput: 287208 bytes/s
DMA throughput: 850809 bytes/s
Faster method: DMA
DMA throughput improvement: 196%

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
```

The README is updated whenever a feature changes the behavior, measurements, or
capabilities of the firmware so that it reflects the current state of the
project.