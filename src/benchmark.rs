use core::num::NonZeroU32;

use embassy_stm32::spi::Error;

use crate::timer::BenchmarkTimer;
use crate::transfer::SpiTransfer;

/// Result produced by a single SPI write benchmark.
pub struct BenchmarkResult {
    transferred_bytes: usize,
    elapsed_microseconds: u64,
}

impl BenchmarkResult {
    pub const fn transferred_bytes(&self) -> usize {
        self.transferred_bytes
    }

    pub const fn elapsed_microseconds(&self) -> u64 {
        self.elapsed_microseconds
    }

    /// Calculates transfer throughput in bytes per second.
    ///
    /// Returns `None` when the measured duration is zero.
    pub fn throughput_bytes_per_second(&self) -> Option<u64> {
        if self.elapsed_microseconds == 0 {
            return None;
        }

        Some((self.transferred_bytes as u64).saturating_mul(1_000_000) / self.elapsed_microseconds)
    }
}

/// Result produced by repeatedly benchmarking an SPI write.
pub struct BenchmarkSummary {
    iterations: u32,
    bytes_per_iteration: usize,
    total_elapsed_microseconds: u64,
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

    pub fn average_elapsed_microseconds(&self) -> u64 {
        self.total_elapsed_microseconds / self.iterations as u64
    }

    pub fn throughput_bytes_per_second(&self) -> Option<u64> {
        if self.total_elapsed_microseconds == 0 {
            return None;
        }

        Some(self.total_bytes().saturating_mul(1_000_000) / self.total_elapsed_microseconds)
    }
}

/// Executes SPI transfer benchmarks.
pub struct SpiBenchmark;

impl SpiBenchmark {
    /// Measures one SPI write operation.
    pub fn run_write<T>(transfer: &mut T, data: &[u8]) -> Result<BenchmarkResult, Error>
    where
        T: SpiTransfer,
    {
        let timer = BenchmarkTimer::start();

        transfer.write(data)?;

        let elapsed = timer.elapsed();

        Ok(BenchmarkResult {
            transferred_bytes: data.len(),
            elapsed_microseconds: elapsed.as_micros(),
        })
    }

    /// Measures repeated SPI write operations.
    pub fn run_repeated_write<T>(
        transfer: &mut T,
        data: &[u8],
        iterations: NonZeroU32,
    ) -> Result<BenchmarkSummary, Error>
    where
        T: SpiTransfer,
    {
        let timer = BenchmarkTimer::start();

        for _ in 0..iterations.get() {
            transfer.write(data)?;
        }

        let elapsed = timer.elapsed();

        Ok(BenchmarkSummary {
            iterations: iterations.get(),
            bytes_per_iteration: data.len(),
            total_elapsed_microseconds: elapsed.as_micros(),
        })
    }
}
