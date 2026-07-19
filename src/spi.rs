use embassy_stm32::Peripherals;
use embassy_stm32::gpio::{Level, Output, Speed};
use embassy_stm32::mode::Blocking;
use embassy_stm32::spi::{Config, Spi};
use embassy_stm32::time::Hertz;

pub struct BlockingSpi<'d> {
    pub spi: Spi<'d, Blocking>,
    pub chip_select: Output<'d>,
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
}
