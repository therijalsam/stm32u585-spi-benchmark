#![no_std]
#![no_main]

mod benchmark;
mod spi;
mod timer;
mod transfer;

use benchmark::{BenchmarkConfig, SpiBenchmark};
use core::num::NonZeroU32;
use defmt::{error, info};
use defmt_rtt as _;
use embassy_executor::Spawner;
use panic_probe as _;
use transfer::SpiTransfer;

fn run_benchmark<T>(spi: &mut T, data: &[u8], config: &BenchmarkConfig)
where
    T: SpiTransfer,
{
    match SpiBenchmark::run_repeated_write(spi, data, config) {
        Ok(result) => {
            info!("------------------------------------");

            info!("Payload size: {} bytes", result.bytes_per_iteration());

            info!("Iterations: {}", result.iterations());

            info!("Total bytes: {}", result.total_bytes());

            info!(
                "Total elapsed time: {} us",
                result.total_elapsed_microseconds()
            );

            info!(
                "Aggregate average time per transfer: {} us",
                result.average_elapsed_microseconds()
            );

            info!(
                "Measured minimum time per transfer: {} us",
                result.min_elapsed_microseconds()
            );

            info!(
                "Measured maximum time per transfer: {} us",
                result.max_elapsed_microseconds()
            );

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
            error!("SPI benchmark failed: {:?}", error);
        }
    }
}

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let peripherals = embassy_stm32::init(Default::default());

    let mut spi = spi::BenchmarkSpi::new(peripherals);

    info!("====================================");
    info!("STM32U585 SPI Benchmark");
    info!("Firmware started");
    info!("SPI1 initialized at 1 MHz");
    info!("====================================");

    let config =
        BenchmarkConfig::new(NonZeroU32::new(100).expect("benchmark iterations must be non-zero"));

    let data_4 = [0xAA; 4];
    let data_16 = [0xAA; 16];
    let data_64 = [0xAA; 64];
    let data_256 = [0xAA; 256];

    run_benchmark(&mut spi, &data_4, &config);
    run_benchmark(&mut spi, &data_16, &config);
    run_benchmark(&mut spi, &data_64, &config);
    run_benchmark(&mut spi, &data_256, &config);

    info!("====================================");
    info!("Blocking SPI benchmarks complete");
    info!("Starting DMA SPI test");
    info!("====================================");

    let dma_test_data = [0xAA; 64];

    match spi.dma_write(&dma_test_data).await {
        Ok(()) => {
            info!("DMA SPI write completed");
            info!("DMA test bytes: {}", dma_test_data.len());
        }

        Err(error) => {
            error!("DMA SPI write failed: {:?}", error);
        }
    }

    info!("====================================");
    info!("Benchmark complete");
    info!("====================================");

    loop {
        cortex_m::asm::nop();
    }
}
