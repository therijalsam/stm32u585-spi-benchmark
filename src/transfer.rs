use embassy_stm32::spi::Error;

/// Common interface for SPI transmit implementations.
pub trait SpiTransfer {
    fn write(&mut self, data: &[u8]) -> Result<(), Error>;
}
