# STM32U585 SPI Benchmark

A small embedded Rust project for measuring SPI transfer performance on an STM32U585.

I'm developing and testing this on the MM6108-EKH05 board using Embassy and probe-rs.

The project currently implements blocking SPI communication and measures transfer time and throughput over repeated SPI writes.
## Goal

The goal of this project is to build a reusable SPI performance benchmarking framework for the STM32U585 and use it to understand how different SPI transfer methods behave in a real embedded system.

I want to measure and compare:

- transfer latency
- throughput
- CPU overhead
- repeated-transfer performance

The project currently focuses on blocking SPI transfers. As the project grows, the same benchmark framework will be used to compare blocking, interrupt-driven, and DMA-based SPI communication.

The main purpose is not just to make SPI work, but to understand the performance trade-offs between different transfer methods and determine which approach is more appropriate for high-speed embedded applications.

## Hardware

- MM6108-EKH05
- STM32U585
- ST-LINK V3

### SPI1 Pins

| Signal | Pin |
|--------|-----|
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
- Software-controlled chip select
- Common `SpiTransfer` interface
- Benchmark timer
- SPI transfer timing
- Throughput calculation
- Repeated SPI benchmarking
- Multiple SPI payload size benchmarking
- Minimum and maximum per-transfer timing
- DMA-backed SPI writes


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

Initializes the STM32 peripherals, creates the SPI driver, runs the benchmark, and prints the results.

### `spi.rs`

### `spi.rs`

Contains the SPI1 implementation and chip-select handling.

The SPI driver supports:

- blocking SPI writes
- DMA-backed asynchronous SPI writes
- software-controlled chip select

### `transfer.rs`

Defines the common interface used by the benchmark code:

```rust
pub trait SpiTransfer {
    fn write(
        &mut self,
        data: &[u8],
    ) -> Result<(), embassy_stm32::spi::Error>;
}
```

This keeps the benchmark logic separate from the SPI hardware implementation.

### `timer.rs`

Contains the timer used to measure SPI transfer duration.

### `benchmark.rs`

Contains the benchmark configuration, execution logic, and calculations for:

- benchmark iterations
- bytes transferred
- total elapsed time
- average transfer time
- throughput

## DMA SPI

The SPI driver now supports DMA-backed asynchronous writes using Embassy.

A 64-byte DMA transfer was successfully executed on the STM32U585:

```text
Starting DMA SPI test
DMA SPI write completed
DMA test bytes: 64

## Current Benchmark

The current benchmark measures repeated blocking SPI transfers using multiple payload sizes.

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

### Results

One benchmark run produced:

| Payload | Total Time | Aggregate Avg / Transfer | Measured Min | Measured Max | Throughput |
|--------:|-----------:|-------------------------:|-------------:|-------------:|-----------:|
| 4 B | 10,415 us | 104 us | 113 us | 113 us | 38,406 bytes/s |
| 16 B | 26,951 us | 269 us | 277 us | 278 us | 59,366 bytes/s |
| 64 B | 93,035 us | 930 us | 937 us | 978 us | 68,791 bytes/s |
| 256 B | 357,353 us | 3,573 us | 3,577 us | 3,618 us | 71,637 bytes/s |

The aggregate average and throughput are measured using one timer around the
complete set of repeated SPI transfers.

Minimum and maximum values are collected separately by timing individual SPI
transfers. Because individual timing introduces additional measurement
overhead, the measured minimum can be slightly higher than the aggregate
average per transfer.

## Throughput

Throughput is calculated from the total number of transferred bytes and the total elapsed time.

```text
throughput = total_bytes × 1,000,000 / elapsed_time_us
```

For the example above:

```text
400 × 1,000,000 / 9040
≈ 44,247 bytes/s
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

Repeated blocking SPI benchmark completed
Iterations: 100
Bytes per iteration: 4
Total bytes: 400
Total elapsed time: 9040 us
Average time per transfer: 90 us
Aggregate throughput: 44247 bytes/s
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
```

The README is updated whenever a new feature is merged so that it reflects the current state of the project.