#![no_std]
#![no_main]

mod timer;

use defmt::info;
use defmt_rtt as _;
use embassy_executor::Spawner;
use panic_probe as _;

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let _peripherals = embassy_stm32::init(Default::default());
    let _timer = timer::BenchmarkTimer::new();

    info!("====================================");
    info!("STM32U585 SPI Benchmark");
    info!("Firmware started");
    info!("====================================");

    loop {
        cortex_m::asm::nop();
    }
}