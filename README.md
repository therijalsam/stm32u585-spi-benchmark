# STM32U585 SPI Benchmark

An embedded Rust project for measuring and comparing SPI transfer performance on an STM32U585.

I'm developing and testing this on the MM6108-EKH05 board using Embassy and probe-rs.

The project currently benchmarks blocking and DMA-backed SPI transfers across different payload sizes and measures transfer time, throughput, and timing variation.

## Goal

The goal of this project is to build a reusable SPI performance benchmarking framework for the STM32U585 and use it to understand how different SPI transfer methods behave in a real embedded system.

I want to measure and compare:

- transfer latency
- throughput
- CPU overhead
- repeated-transfer performance
- performance across different payload sizes

The main purpose is not just to make SPI communication work, but to understand the performance trade-offs between different transfer methods and determine which approach is more appropriate for high-speed embedded applications.

## Hardware

- MM6108-EKH05
- STM32U585
- ST-LINK V3

### SPI1 Pins

| Signal | Pin |
| ------ | --- |
| SCK | PE13 |
| MISO | PE14 |
| MOSI | PE15 |
| CS | PE12 |

Chip select is controlled in software using PE12.

The SPI clock is currently configured at:

```text
1 MHz
```

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
- Blocking vs DMA performance comparison
- CPU task concurrency during DMA transfers
- Automatic blocking vs DMA throughput comparison

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

Initializes the STM32 peripherals, creates the SPI driver, runs the blocking and
DMA benchmarks, measures background task progress during each transfer method,
automatically compares blocking and DMA throughput for each payload size
and prints the results through `defmt`.

### `spi.rs`

Contains the SPI1 implementation and chip-select handling.

The SPI driver supports:

- blocking SPI writes
- DMA-backed asynchronous SPI writes
- software-controlled chip select

### `transfer.rs`

Defines the interfaces used by the benchmark code.

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

This keeps the benchmark logic separate from the SPI hardware implementation.

### `timer.rs`

Contains the timer used to measure SPI transfer duration.

### `benchmark.rs`

Contains the benchmark configuration and execution logic for both blocking and DMA transfers.

It calculates:

- benchmark iterations
- bytes transferred
- total elapsed time
- aggregate average transfer time
- minimum transfer time
- maximum transfer time
- throughput

## Current Benchmark

The current benchmark compares blocking SPI and DMA-backed SPI transfers using multiple payload sizes.

SPI1 is configured at 1 MHz, and each payload is transferred 100 times.

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

Both transfer methods use the same payload sizes and iteration counts so their performance can be compared directly.

## Blocking SPI Results

One benchmark run produced:

| Payload | Total Time | Aggregate Avg | Measured Min | Measured Max | Throughput |
|--------:|-----------:|--------------:|-------------:|-------------:|-----------:|
| 4 B | 10,416 us | 104 us | 112 us | 112 us | 38,402 bytes/s |
| 16 B | 26,952 us | 269 us | 277 us | 318 us | 59,364 bytes/s |
| 64 B | 93,034 us | 930 us | 937 us | 978 us | 68,792 bytes/s |
| 256 B | 357,352 us | 3,573 us | 3,577 us | 3,618 us | 71,638 bytes/s |

## DMA SPI Results

| Payload | Total Time | Aggregate Avg | Measured Min | Measured Max | Throughput |
|--------:|-----------:|--------------:|-------------:|-------------:|-----------:|
| 4 B | 18,752 us | 187 us | 195 us | 236 us | 21,331 bytes/s |
| 16 B | 27,991 us | 279 us | 289 us | 326 us | 57,161 bytes/s |
| 64 B | 61,788 us | 617 us | 626 us | 650 us | 103,579 bytes/s |
| 256 B | 215,392 us | 2,153 us | 2,162 us | 2,162 us | 118,853 bytes/s |

## Blocking vs DMA

| Payload | Blocking Throughput | DMA Throughput | Faster |
|--------:|--------------------:|---------------:|:------|
| 4 B | 38,402 bytes/s | 21,331 bytes/s | Blocking |
| 16 B | 59,364 bytes/s | 57,161 bytes/s | Blocking |
| 64 B | 68,792 bytes/s | 103,579 bytes/s | DMA |
| 256 B | 71,638 bytes/s | 118,853 bytes/s | DMA |

The results show that DMA is not automatically faster for small SPI transfers.

For the 4-byte payload, blocking SPI performs better because the DMA transfer introduces additional setup and asynchronous execution overhead.

At 16 bytes, the two approaches perform similarly.

At larger payload sizes, DMA becomes significantly faster. For the 64-byte transfer, DMA reaches about 1.5 times the blocking throughput. For the 256-byte transfer, DMA reaches about 1.66 times the blocking throughput.

With the current implementation, the performance crossover between blocking and DMA occurs somewhere between 16 and 64 bytes.

### Automatic Comparison

The firmware automatically compares blocking and DMA throughput after both
benchmark sets complete.

For each payload size, it reports:

- blocking throughput
- DMA throughput
- the faster transfer method
- approximate throughput improvement

A run with the background concurrency task enabled produced:

| Payload | Blocking Throughput | DMA Throughput | Faster Method | Throughput Improvement |
|--------:|--------------------:|---------------:|:--------------|-----------------------:|
| 4 B | 38,413 bytes/s | 21,343 bytes/s | Blocking | 79% |
| 16 B | 59,364 bytes/s | 49,280 bytes/s | Blocking | 20% |
| 64 B | 68,792 bytes/s | 98,010 bytes/s | DMA | 42% |
| 256 B | 71,646 bytes/s | 114,726 bytes/s | DMA | 60% |

The results show a clear change in which transfer method performs better as
payload size increases.

For 4-byte and 16-byte transfers, blocking SPI provides higher throughput.
For 64-byte and 256-byte transfers, DMA provides higher throughput.

With the payload sizes currently tested, the performance crossover occurs
between 16 and 64 bytes.

These measurements were collected while the background Embassy task was
enabled. Because that task executes concurrently with DMA transfers, the DMA
throughput values can be slightly lower than the baseline throughput results
measured without the concurrency workload.

## CPU Concurrency Test

In addition to transfer performance, the firmware checks whether another
application task can make progress while SPI communication is active.

A background Embassy task increments a counter approximately once every
millisecond.

One test run produced:

| Transfer Method | Background Task Progress |
|:----------------|-------------------------:|
| Blocking SPI | 0 |
| DMA SPI | 553 |

During the blocking SPI benchmark, the background task made no progress because
the blocking transfers kept control of the executor.

During the DMA-backed asynchronous benchmark, the background task executed 553
times while SPI communication was in progress.

This demonstrates that DMA-backed asynchronous SPI allows other Embassy tasks
to make progress while a transfer is being handled by DMA.

The counter is not a CPU utilization percentage. It only indicates whether
another task was able to execute during the benchmark.


## Timing Method

Aggregate timing is measured using one timer around the complete set of repeated SPI transfers.

```text
start timer

transfer
transfer
transfer
...
100 transfers

stop timer
```

The aggregate average is calculated from:

```text
total elapsed time / number of iterations
```

Minimum and maximum transfer times are measured separately by timing individual transfers.

Because individual timing introduces additional measurement overhead, the measured minimum can be slightly higher than the aggregate average.

## Throughput

Throughput is calculated using:

```text
throughput = total_bytes × 1,000,000 / elapsed_time_us
```

For example, the 256-byte DMA benchmark transferred:

```text
25,600 bytes
```

in:

```text
215,392 us
```

which gives approximately:

```text
118,853 bytes/s
```

## Build

Install the Rust target:

```bash
rustup target add thumbv8m.main-none-eabihf
```

Build the project:

```bash
cargo build
```

Format the code:

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
SPI1 initialized at 1 MHz

Starting blocking SPI benchmarks

Payload size: 64 bytes
Iterations: 100
Total bytes: 6400
Total elapsed time: 93034 us
Aggregate average time per transfer: 930 us
Measured minimum time per transfer: 937 us
Measured maximum time per transfer: 978 us
Throughput: 68792 bytes/s

Blocking SPI benchmarks complete
Starting DMA SPI benchmarks

DMA payload size: 64 bytes
Iterations: 100
Total bytes: 6400
Total elapsed time: 61788 us
Aggregate average time per transfer: 617 us
Measured minimum time per transfer: 626 us
Measured maximum time per transfer: 650 us
DMA throughput: 103579 bytes/s

DMA SPI benchmarks complete
Benchmark complete
```

## Development

The project is developed using small feature branches.

Each feature is built and tested before being merged into `main`.

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
```

The README is updated when a feature changes the behavior or capabilities of the project so that it reflects the current state of the firmware.