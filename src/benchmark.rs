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
}
