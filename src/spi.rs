use embassy_stm32::Peripherals;
use embassy_stm32::gpio::{Level, Output, Speed};
use embassy_stm32::mode::Blocking;
use embassy_stm32::spi::{Config, Error, Spi};
use embassy_stm32::time::Hertz;

use crate::transfer::SpiTransfer;

pub struct BlockingSpi<'d> {
    spi: Spi<'d, Blocking>,
    chip_select: Output<'d>,
}

impl<'d> BlockingSpi<'d> {
    pub fn new(peripherals: Peripherals) -> Self {
        let mut config = Config::default();
        config.frequency = Hertz(1_000_000);

        let chip_select = Output::new(peripherals.PE12, Level::High, Speed::VeryHigh);

        let spi = Spi::new_blocking(
            peripherals.SPI1,
            peripherals.PE13,
            peripherals.PE15,
            peripherals.PE14,
            config,
        );

        Self { spi, chip_select }
    }

    fn write_internal(&mut self, data: &[u8]) -> Result<(), Error> {
        self.chip_select.set_low();

        let result = self.spi.blocking_write(data);

        self.chip_select.set_high();

        result
    }
}

impl SpiTransfer for BlockingSpi<'_> {
    fn write(&mut self, data: &[u8]) -> Result<(), Error> {
        self.write_internal(data) //write internal contains hardware specific implementation of the write function.
    }
}
