use clap::{Parser, Subcommand};
use missiongraph_rs::{build_trace_skeleton, parse_ast, validate_ast};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Parser)]
#[command(name = "mgl-rs")]
#[command(about = "MissionGraph Rust runtime bootstrap CLI", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Debug, Subcommand)]
enum Commands {
    /// Validate a MissionGraph AST JSON document against bootstrap checks.
    CheckAst {
        /// Path to AST JSON file (for example output of `mgl parse`).
        ast: PathBuf,
    },
    /// Emit a trace skeleton from a MissionGraph AST JSON document.
    TraceSkeleton {
        /// Path to AST JSON file (for example output of `mgl parse`).
        ast: PathBuf,
    },
}

fn main() -> Result<(), String> {
    let cli = Cli::parse();
    match cli.command {
        Commands::CheckAst { ast } => {
            let ast_text = fs::read_to_string(ast)
                .map_err(|err| format!("failed to read AST file: {err}"))?;
            let ast = parse_ast(&ast_text)?;
            validate_ast(&ast)?;
            println!("ok");
            Ok(())
        }
        Commands::TraceSkeleton { ast } => {
            let ast_text = fs::read_to_string(ast)
                .map_err(|err| format!("failed to read AST file: {err}"))?;
            let ast = parse_ast(&ast_text)?;
            validate_ast(&ast)?;
            let trace = build_trace_skeleton(&ast);
            let rendered = serde_json::to_string_pretty(&trace)
                .map_err(|err| format!("failed to serialize trace skeleton: {err}"))?;
            println!("{rendered}");
            Ok(())
        }
    }
}
