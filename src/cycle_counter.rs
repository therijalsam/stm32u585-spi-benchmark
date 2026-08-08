use cortex_m::Peripherals;
use cortex_m::peripheral::DWT;

/// Provides access to the Cortex-M DWT hardware cycle counter.
pub struct CycleCounter;

impl CycleCounter {
    /// Initializes the DWT cycle counter.
    pub fn initialize() {
        let mut core = Peripherals::take().expect("Cortex-M core peripherals already taken");

        if !DWT::has_cycle_counter() {
            panic!("DWT cycle counter is not available");
        }

        core.DCB.enable_trace();

        core.DWT.set_cycle_count(0);
        core.DWT.enable_cycle_counter();
    }

    /// Returns the current cycle-counter value.
    pub fn current() -> u32 {
        DWT::cycle_count()
    }

    /// Calculates elapsed cycles using wrapping arithmetic.
    pub fn elapsed_since(start: u32) -> u32 {
        Self::current().wrapping_sub(start)
    }
}
