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

Contains the blocking SPI1 implementation and chip-select handling.

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

Contains the benchmark logic and calculations for:

- iterations
- bytes transferred
- total elapsed time
- average transfer time
- throughput

## Current Benchmark

The current test repeatedly writes four bytes over SPI.

```rust
let test_data = [0xAA, 0x55, 0x12, 0x34];
```

The transfer is repeated 100 times.

That means:

```text
4 bytes × 100 iterations = 400 bytes
```

One test run produced:

```text
Repeated blocking SPI benchmark completed
Iterations: 100
Bytes per iteration: 4
Total bytes: 400
Total elapsed time: 9040 us
Average time per transfer: 90 us
Aggregate throughput: 44247 bytes/s
```

The numbers may change between runs depending on the hardware and measurement conditions.

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