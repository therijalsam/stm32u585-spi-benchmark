use core::num::NonZeroU32;

use embassy_stm32::spi::Error;

use crate::cycle_counter::CycleCounter;
use crate::timer::BenchmarkTimer;
use crate::transfer::{DmaTransfer, SpiTransfer};

/// Configuration used when running an SPI benchmark.
pub struct BenchmarkConfig {
    iterations: NonZeroU32,
}

impl BenchmarkConfig {
    pub const fn new(iterations: NonZeroU32) -> Self {
        Self { iterations }
    }

    pub const fn iterations(&self) -> NonZeroU32 {
        self.iterations
    }
}

/// Result produced by repeatedly benchmarking an SPI write.
pub struct BenchmarkSummary {
    iterations: u32,
    bytes_per_iteration: usize,
    total_elapsed_microseconds: u64,
    total_elapsed_cycles: u64,
    min_elapsed_microseconds: u64,
    max_elapsed_microseconds: u64,
}

impl BenchmarkSummary {
    pub const fn iterations(&self) -> u32 {
        self.iterations
    }

    pub const fn bytes_per_iteration(&self) -> usize {
        self.bytes_per_iteration
    }

    pub fn total_bytes(&self) -> u64 {
        (self.bytes_per_iteration as u64).saturating_mul(self.iterations as u64)
    }

    pub const fn total_elapsed_microseconds(&self) -> u64 {
        self.total_elapsed_microseconds
    }

    pub const fn total_elapsed_cycles(&self) -> u64 {
        self.total_elapsed_cycles
    }

    pub fn average_elapsed_microseconds(&self) -> u64 {
        self.total_elapsed_microseconds / self.iterations as u64
    }

    pub fn average_cycles_per_transfer(&self) -> u64 {
        self.total_elapsed_cycles / self.iterations as u64
    }

    pub fn throughput_bytes_per_second(&self) -> Option<u64> {
        if self.total_elapsed_microseconds == 0 {
            return None;
        }

        Some(self.total_bytes().saturating_mul(1_000_000) / self.total_elapsed_microseconds)
    }

    pub const fn min_elapsed_microseconds(&self) -> u64 {
        self.min_elapsed_microseconds
    }

    pub const fn max_elapsed_microseconds(&self) -> u64 {
        self.max_elapsed_microseconds
    }
}

/// Executes SPI transfer benchmarks.
pub struct SpiBenchmark;

impl SpiBenchmark {
    /// Measures repeated SPI write operations.
    pub fn run_repeated_write<T>(
        transfer: &mut T,
        data: &[u8],
        config: &BenchmarkConfig,
    ) -> Result<BenchmarkSummary, Error>
    where
        T: SpiTransfer,
    {
        let iterations = config.iterations().get();

        let start_cycles = CycleCounter::current();

        let total_timer = BenchmarkTimer::start();

        for _ in 0..iterations {
            transfer.write(data)?;
        }

        let total_elapsed_microseconds = total_timer.elapsed().as_micros();

        let total_elapsed_cycles = CycleCounter::elapsed_since(start_cycles) as u64;

        let mut min_elapsed_microseconds = u64::MAX;
        let mut max_elapsed_microseconds = 0;

        for _ in 0..iterations {
            let transfer_timer = BenchmarkTimer::start();

            transfer.write(data)?;

            let transfer_elapsed = transfer_timer.elapsed().as_micros();

            min_elapsed_microseconds = min_elapsed_microseconds.min(transfer_elapsed);

            max_elapsed_microseconds = max_elapsed_microseconds.max(transfer_elapsed);
        }

        Ok(BenchmarkSummary {
            iterations,
            bytes_per_iteration: data.len(),
            total_elapsed_microseconds,
            total_elapsed_cycles,
            min_elapsed_microseconds,
            max_elapsed_microseconds,
        })
    }

    pub async fn run_repeated_dma_write<T>(
        transfer: &mut T,
        data: &[u8],
        config: &BenchmarkConfig,
    ) -> Result<BenchmarkSummary, Error>
    where
        T: DmaTransfer,
    {
        let iterations = config.iterations().get();

        let start_cycles = CycleCounter::current();

        let total_timer = BenchmarkTimer::start();

        for _ in 0..iterations {
            transfer.write_dma(data).await?;
        }

        let total_elapsed_microseconds = total_timer.elapsed().as_micros();

        let total_elapsed_cycles = CycleCounter::elapsed_since(start_cycles) as u64;

        let mut min_elapsed_microseconds = u64::MAX;
        let mut max_elapsed_microseconds = 0;

        for _ in 0..iterations {
            let transfer_timer = BenchmarkTimer::start();

            transfer.write_dma(data).await?;

            let transfer_elapsed = transfer_timer.elapsed().as_micros();

            min_elapsed_microseconds = min_elapsed_microseconds.min(transfer_elapsed);

            max_elapsed_microseconds = max_elapsed_microseconds.max(transfer_elapsed);
        }

        Ok(BenchmarkSummary {
            iterations,
            bytes_per_iteration: data.len(),
            total_elapsed_microseconds,
            total_elapsed_cycles,
            min_elapsed_microseconds,
            max_elapsed_microseconds,
        })
    }
}
