use std::{env, fs, path::PathBuf};

fn main() {
    let output_directory = PathBuf::from(
        env::var_os("OUT_DIR")
            .expect("OUT_DIR environment variable is missing"),
    );

    fs::copy("memory.x", output_directory.join("memory.x"))
        .expect("Failed to copy memory.x");

    println!(
        "cargo:rustc-link-search={}",
        output_directory.display()
    );

    println!("cargo:rerun-if-changed=memory.x");
}