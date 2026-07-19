use embassy_time::{Duration, Instant};

/// Measures elapsed execution time using Embassy's system timer.
pub struct BenchmarkTimer {
    started_at: Instant,
}

impl BenchmarkTimer {
    /// Creates and immediately starts a new benchmark timer.
    pub fn start() -> Self {
        Self {
            started_at: Instant::now(),
        }
    }

    /// Returns the time elapsed since the timer started.
    pub fn elapsed(&self) -> Duration {
        self.started_at.elapsed()
    }
}
