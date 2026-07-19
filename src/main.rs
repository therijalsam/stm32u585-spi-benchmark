#![no_std]
#![no_main]

mod spi;
mod timer;

use defmt::info;
use defmt_rtt as _;
use embassy_executor::Spawner;
use panic_probe as _;

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let peripherals = embassy_stm32::init(Default::default());

    let _timer = timer::BenchmarkTimer::new();
    let _spi = spi::BlockingSpi::new(peripherals);

    info!("====================================");
    info!("STM32U585 SPI Benchmark");
    info!("Firmware started");
    info!("SPI1 initialized at 1 MHz");
    info!("SCK  = PE13");
    info!("MISO = PE14");
    info!("MOSI = PE15");
    info!("CS   = PE12");
    info!("====================================");

    loop {
        cortex_m::asm::nop();
    }
}
