#![no_std]
#![no_main]

mod benchmark;
mod spi;
mod timer;
mod transfer;

use benchmark::SpiBenchmark;
use core::num::NonZeroU32;
use defmt::{error, info};
use defmt_rtt as _;
use embassy_executor::Spawner;
use panic_probe as _;

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let peripherals = embassy_stm32::init(Default::default());
    let mut spi = spi::BlockingSpi::new(peripherals);

    info!("====================================");
    info!("STM32U585 SPI Benchmark");
    info!("Firmware started");
    info!("SPI1 initialized at 1 MHz");
    info!("====================================");

    let test_data = [0xAA, 0x55, 0x12, 0x34];

    let iterations = NonZeroU32::new(100).expect("benchmark iterations must be non-zero");

    match SpiBenchmark::run_repeated_write(&mut spi, &test_data, iterations) {
        Ok(result) => {
            info!("Repeated blocking SPI benchmark completed");

            info!("Iterations: {}", result.iterations());

            info!("Bytes per iteration: {}", result.bytes_per_iteration());

            info!("Total bytes: {}", result.total_bytes());

            info!(
                "Total elapsed time: {} us",
                result.total_elapsed_microseconds()
            );

            info!(
                "Average time per transfer: {} us",
                result.average_elapsed_microseconds()
            );

            match result.throughput_bytes_per_second() {
                Some(throughput) => {
                    info!("Aggregate throughput: {} bytes/s", throughput);
                }
                None => {
                    error!("Unable to calculate throughput: elapsed time is zero");
                }
            }
        }

        Err(error) => {
            error!("Repeated SPI benchmark failed: {:?}", error);
        }
    }

    loop {
        cortex_m::asm::nop();
    }
}
