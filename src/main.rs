#![no_std]
#![no_main]

mod benchmark;
mod spi;
mod timer;
mod transfer;

use benchmark::SpiBenchmark;
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

    match SpiBenchmark::run_write(&mut spi, &test_data) {
        Ok(result) => {
            info!("Blocking SPI write completed");
            info!("Transferred bytes: {}", result.transferred_bytes());
            info!("Elapsed time: {} us", result.elapsed_microseconds());

            match result.throughput_bytes_per_second() {
                Some(throughput) => {
                    info!("Throughput: {} bytes/s", throughput);
                }
                None => {
                    error!("Unable to calculate throughput: elapsed time is zero");
                }
            }
        }
        Err(error) => {
            error!("Blocking SPI write failed: {:?}", error);
        }
    }

    loop {
        cortex_m::asm::nop();
    }
}
