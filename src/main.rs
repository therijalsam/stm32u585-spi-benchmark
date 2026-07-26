#![no_std]
#![no_main]

mod spi;
mod timer;
mod transfer;

use defmt::{error, info};
use defmt_rtt as _;
use embassy_executor::Spawner;
use panic_probe as _;

use timer::BenchmarkTimer;
use transfer::SpiTransfer;

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let peripherals = embassy_stm32::init(Default::default());
    let mut spi = spi::BlockingSpi::new(peripherals);

    info!("====================================");
    info!("STM32U585 SPI Benchmark");
    info!("Firmware started");
    info!("SPI1 initialized at 1 MHz");
    info!("====================================");

    let test_data: [u8; 4] = [0xAA, 0x55, 0x12, 0x34];

    let timer = BenchmarkTimer::start();
    let write_result = spi.write(&test_data);
    let elapsed = timer.elapsed();

    match write_result {
        Ok(()) => {
            info!("Blocking SPI write completed");
            info!("Transferred bytes: {}", test_data.len());
            info!("Elapsed time: {} us", elapsed.as_micros());
        }
        Err(error) => {
            error!("Blocking SPI write failed: {:?}", error);
        }
    }

    loop {
        cortex_m::asm::nop();
    }
}
