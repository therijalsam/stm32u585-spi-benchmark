#![no_std]
#![no_main]

mod benchmark;
mod spi;
mod timer;
mod transfer;

use benchmark::{BenchmarkConfig, SpiBenchmark};
use core::num::NonZeroU32;
use core::sync::atomic::{AtomicU32, Ordering};
use defmt::{error, info};
use defmt_rtt as _;
use embassy_executor::Spawner;
use embassy_time::Timer;
use panic_probe as _;
use transfer::{DmaTransfer, SpiTransfer};

static CPU_ACTIVITY: AtomicU32 = AtomicU32::new(0);

const SPI_FREQUENCIES: [u32; 4] = [1_000_000, 2_000_000, 4_000_000, 8_000_000];

#[embassy_executor::task]
async fn cpu_activity_task() {
    loop {
        CPU_ACTIVITY.fetch_add(1, Ordering::Relaxed);

        Timer::after_millis(1).await;
    }
}

fn run_benchmark<T>(spi: &mut T, data: &[u8], config: &BenchmarkConfig) -> Option<u64>
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

            let throughput = result.throughput_bytes_per_second();

            match throughput {
                Some(throughput) => {
                    info!("Throughput: {} bytes/s", throughput);
                }

                None => {
                    error!("Unable to calculate throughput: elapsed time is zero");
                }
            }

            throughput
        }

        Err(error) => {
            error!("SPI benchmark failed: {:?}", error);
            None
        }
    }
}

async fn run_dma_benchmark<T>(spi: &mut T, data: &[u8], config: &BenchmarkConfig) -> Option<u64>
where
    T: DmaTransfer,
{
    match SpiBenchmark::run_repeated_dma_write(spi, data, config).await {
        Ok(result) => {
            info!("------------------------------------");

            info!("DMA payload size: {} bytes", result.bytes_per_iteration());

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

            let throughput = result.throughput_bytes_per_second();

            match throughput {
                Some(throughput) => {
                    info!("DMA throughput: {} bytes/s", throughput);
                }

                None => {
                    error!("Unable to calculate DMA throughput: elapsed time is zero");
                }
            }

            throughput
        }

        Err(error) => {
            error!("DMA SPI benchmark failed: {:?}", error);
            None
        }
    }
}

fn print_comparison(
    payload_size: usize,
    blocking_throughput: Option<u64>,
    dma_throughput: Option<u64>,
) {
    info!("------------------------------------");
    info!("Comparison for {} byte payload", payload_size);

    match (blocking_throughput, dma_throughput) {
        (Some(blocking), Some(dma)) => {
            info!("Blocking throughput: {} bytes/s", blocking);
            info!("DMA throughput: {} bytes/s", dma);

            if blocking == 0 || dma == 0 {
                error!("Unable to calculate throughput improvement");
                return;
            }

            if dma > blocking {
                let improvement = (dma - blocking).saturating_mul(100) / blocking;

                info!("Faster method: DMA");
                info!("DMA throughput improvement: {}%", improvement);
            } else if blocking > dma {
                let improvement = (blocking - dma).saturating_mul(100) / dma;

                info!("Faster method: Blocking");
                info!("Blocking throughput improvement: {}%", improvement);
            } else {
                info!("Faster method: Equal");
            }
        }

        _ => {
            error!(
                "Unable to compare transfer methods for {} byte payload",
                payload_size
            );
        }
    }
}

async fn run_clock_benchmark(
    spi: &mut spi::BenchmarkSpi<'_>,
    requested_frequency: u32,
    config: &BenchmarkConfig,
) {
    info!("====================================");
    info!("Requested SPI frequency: {} Hz", requested_frequency);
    info!(
        "Maximum supported SPI frequency: {} Hz",
        spi.maximum_frequency()
    );

    let actual_frequency = match spi.set_frequency(requested_frequency) {
        Ok(frequency) => frequency,

        Err(_) => {
            error!(
                "Skipping unsupported SPI frequency: {} Hz",
                requested_frequency
            );
            return;
        }
    };

    info!("Actual SPI frequency: {} Hz", actual_frequency);
    info!("====================================");

    let data_4 = [0xAA; 4];
    let data_16 = [0xAA; 16];
    let data_64 = [0xAA; 64];
    let data_256 = [0xAA; 256];

    CPU_ACTIVITY.store(0, Ordering::Relaxed);

    info!("====================================");
    info!("Starting blocking SPI benchmarks");
    info!("SPI frequency: {} Hz", actual_frequency);
    info!("====================================");

    let blocking_4 = run_benchmark(spi, &data_4, config);

    let blocking_16 = run_benchmark(spi, &data_16, config);

    let blocking_64 = run_benchmark(spi, &data_64, config);

    let blocking_256 = run_benchmark(spi, &data_256, config);

    let blocking_cpu_activity = CPU_ACTIVITY.load(Ordering::Relaxed);

    info!(
        "CPU worker progress during blocking: {}",
        blocking_cpu_activity
    );

    CPU_ACTIVITY.store(0, Ordering::Relaxed);

    info!("====================================");
    info!("Starting DMA SPI benchmarks");
    info!("SPI frequency: {} Hz", actual_frequency);
    info!("====================================");

    let dma_4 = run_dma_benchmark(spi, &data_4, config).await;

    let dma_16 = run_dma_benchmark(spi, &data_16, config).await;

    let dma_64 = run_dma_benchmark(spi, &data_64, config).await;

    let dma_256 = run_dma_benchmark(spi, &data_256, config).await;

    let dma_cpu_activity = CPU_ACTIVITY.load(Ordering::Relaxed);

    info!("CPU worker progress during DMA: {}", dma_cpu_activity);

    info!("====================================");
    info!("Blocking vs DMA comparison");
    info!("SPI frequency: {} Hz", actual_frequency);
    info!("====================================");

    print_comparison(4, blocking_4, dma_4);
    print_comparison(16, blocking_16, dma_16);
    print_comparison(64, blocking_64, dma_64);
    print_comparison(256, blocking_256, dma_256);

    info!("====================================");
    info!("Benchmark complete for {} Hz", actual_frequency);
    info!("====================================");
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let mut mcu_config = embassy_stm32::Config::default();

    mcu_config.rcc.hsi = true;
    mcu_config.rcc.sys = embassy_stm32::rcc::Sysclk::HSI;

    let peripherals = embassy_stm32::init(mcu_config);

    let mut spi = spi::BenchmarkSpi::new(peripherals);

    spawner.spawn(cpu_activity_task()).unwrap();

    Timer::after_millis(10).await;

    info!("====================================");
    info!("STM32U585 SPI Benchmark");
    info!("Firmware started");
    info!("SPI1 maximum frequency: {} Hz", spi.maximum_frequency());
    info!("====================================");

    let config =
        BenchmarkConfig::new(NonZeroU32::new(100).expect("benchmark iterations must be non-zero"));

    for frequency in SPI_FREQUENCIES {
        run_clock_benchmark(&mut spi, frequency, &config).await;
    }

    info!("====================================");
    info!("SPI clock benchmarks complete");
    info!("Benchmark complete");
    info!("====================================");

    loop {
        cortex_m::asm::nop();
    }
}
