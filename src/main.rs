#![no_std]
#![no_main]

mod benchmark;
mod cycle_counter;
mod spi;
mod timer;
mod transfer;

use benchmark::{BenchmarkConfig, SpiBenchmark};
use core::num::NonZeroU32;
use core::sync::atomic::{AtomicU32, Ordering};
use cycle_counter::CycleCounter;
use defmt::{error, info};
use defmt_rtt as _;
use embassy_executor::Spawner;
use embassy_time::Timer;
use panic_probe as _;
use transfer::{DmaTransfer, SpiTransfer};

static CPU_ACTIVITY: AtomicU32 = AtomicU32::new(0);

const SPI_FREQUENCIES: [u32; 4] = [1_000_000, 2_000_000, 4_000_000, 8_000_000];

const PAYLOAD_SIZES: [usize; 9] = [4, 16, 24, 32, 40, 48, 56, 64, 256];

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
                "Total elapsed core cycles: {}",
                result.total_elapsed_cycles()
            );

            info!(
                "Average core cycles per transfer: {}",
                result.average_cycles_per_transfer()
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
                "Total elapsed core cycles: {}",
                result.total_elapsed_cycles()
            );

            info!(
                "Average core cycles per transfer: {}",
                result.average_cycles_per_transfer()
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

fn print_crossover_summary(
    spi_frequency: u32,
    blocking_results: &[Option<u64>],
    dma_results: &[Option<u64>],
) {
    info!("====================================");

    info!("DMA crossover analysis at {} Hz", spi_frequency);

    info!("====================================");

    let mut crossover_found = false;

    for index in 1..PAYLOAD_SIZES.len() {
        let previous_blocking = blocking_results[index - 1];

        let previous_dma = dma_results[index - 1];

        let current_blocking = blocking_results[index];

        let current_dma = dma_results[index];

        if let (
            Some(previous_blocking),
            Some(previous_dma),
            Some(current_blocking),
            Some(current_dma),
        ) = (
            previous_blocking,
            previous_dma,
            current_blocking,
            current_dma,
        ) {
            let blocking_was_faster = previous_blocking >= previous_dma;

            let dma_is_faster = current_dma > current_blocking;

            if blocking_was_faster && dma_is_faster {
                info!(
                    "DMA crossover detected between {} and {} bytes",
                    PAYLOAD_SIZES[index - 1],
                    PAYLOAD_SIZES[index]
                );

                crossover_found = true;

                break;
            }
        }
    }

    if !crossover_found {
        info!("No blocking-to-DMA crossover detected in tested payload range");
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

    let data = [0xAA; 256];

    CPU_ACTIVITY.store(0, Ordering::Relaxed);

    info!("====================================");
    info!("Starting blocking SPI benchmarks");

    info!("SPI frequency: {} Hz", actual_frequency);

    info!("====================================");

    let mut blocking_results = [None; PAYLOAD_SIZES.len()];

    for (index, payload_size) in PAYLOAD_SIZES.iter().copied().enumerate() {
        blocking_results[index] = run_benchmark(spi, &data[..payload_size], config);
    }

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

    let mut dma_results = [None; PAYLOAD_SIZES.len()];

    for (index, payload_size) in PAYLOAD_SIZES.iter().copied().enumerate() {
        dma_results[index] = run_dma_benchmark(spi, &data[..payload_size], config).await;
    }

    let dma_cpu_activity = CPU_ACTIVITY.load(Ordering::Relaxed);

    info!("CPU worker progress during DMA: {}", dma_cpu_activity);

    info!("====================================");
    info!("Blocking vs DMA comparison");

    info!("SPI frequency: {} Hz", actual_frequency);

    info!("====================================");

    for (index, payload_size) in PAYLOAD_SIZES.iter().copied().enumerate() {
        print_comparison(payload_size, blocking_results[index], dma_results[index]);
    }

    print_crossover_summary(actual_frequency, &blocking_results, &dma_results);

    info!("====================================");

    info!("Benchmark complete for {} Hz", actual_frequency);

    info!("====================================");
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    CycleCounter::initialize();

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
    info!("DWT cycle counter enabled");

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
