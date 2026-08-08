use embassy_stm32::Peripherals;
use embassy_stm32::gpio::{Level, Output, Speed};
use embassy_stm32::mode::Async;
use embassy_stm32::spi::{Config, Error, Spi};
use embassy_stm32::time::Hertz;

use crate::transfer::{DmaTransfer, SpiTransfer};

pub struct BenchmarkSpi<'d> {
    spi: Spi<'d, Async>,
    chip_select: Output<'d>,
}

impl<'d> BenchmarkSpi<'d> {
    pub fn new(peripherals: Peripherals) -> Self {
        let mut config = Config::default();
        config.frequency = Hertz(1_000_000);

        let chip_select = Output::new(peripherals.PE12, Level::High, Speed::VeryHigh);

        let spi = Spi::new(
            peripherals.SPI1,
            peripherals.PE13,
            peripherals.PE15,
            peripherals.PE14,
            peripherals.GPDMA1_CH0,
            peripherals.GPDMA1_CH1,
            config,
        );

        Self { spi, chip_select }
    }

    pub fn set_frequency(&mut self, frequency_hz: u32) -> Result<u32, ()> {
        let maximum_frequency = self.maximum_frequency();

        if frequency_hz == 0 || frequency_hz > maximum_frequency {
            return Err(());
        }

        let mut config = self.spi.get_current_config();

        config.frequency = Hertz(frequency_hz);

        self.spi.set_config(&config)?;

        Ok(self.spi.get_current_config().frequency.0)
    }

    pub fn maximum_frequency(&self) -> u32 {
        embassy_stm32::rcc::frequency::<embassy_stm32::peripherals::SPI1>().0 / 2
    }

    fn write_internal(&mut self, data: &[u8]) -> Result<(), Error> {
        self.chip_select.set_low();

        let result = self.spi.blocking_write(data);

        self.chip_select.set_high();

        result
    }

    pub async fn dma_write(&mut self, data: &[u8]) -> Result<(), Error> {
        self.chip_select.set_low();

        let result = self.spi.write(data).await;

        self.chip_select.set_high();

        result
    }
}

impl SpiTransfer for BenchmarkSpi<'_> {
    fn write(&mut self, data: &[u8]) -> Result<(), Error> {
        self.write_internal(data) //write internal contains hardware specific implementation of the write function.
    }
}

impl DmaTransfer for BenchmarkSpi<'_> {
    async fn write_dma(&mut self, data: &[u8]) -> Result<(), Error> {
        self.dma_write(data).await
    }
}
