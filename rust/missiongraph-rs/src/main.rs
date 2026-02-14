use clap::{Parser, Subcommand};
use missiongraph_rs::{build_trace_skeleton, parse_ast, validate_ast};
use serde::Serialize;
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
        /// Emit machine-readable JSON status payload.
        #[arg(long)]
        json: bool,
    },
    /// Emit a trace skeleton from a MissionGraph AST JSON document.
    TraceSkeleton {
        /// Path to AST JSON file (for example output of `mgl parse`).
        ast: PathBuf,
    },
}

#[derive(Debug, Serialize)]
struct CheckAstReport {
    ok: bool,
    ast_version: Option<String>,
    goal: Option<String>,
    task_count: Option<usize>,
    errors: Vec<String>,
}

fn main() {
    let cli = Cli::parse();
    let exit_code = run(cli);
    std::process::exit(exit_code);
}

fn run(cli: Cli) -> i32 {
    match cli.command {
        Commands::CheckAst { ast, json } => run_check_ast(ast, json),
        Commands::TraceSkeleton { ast } => run_trace_skeleton(ast),
    }
}

fn run_check_ast(ast: PathBuf, json: bool) -> i32 {
    let mut report = CheckAstReport {
        ok: false,
        ast_version: None,
        goal: None,
        task_count: None,
        errors: vec![],
    };

    let ast_text = match fs::read_to_string(&ast) {
        Ok(text) => text,
        Err(err) => {
            report
                .errors
                .push(format!("failed to read AST file '{}': {err}", ast.display()));
            return finish_check_report(report, json);
        }
    };

    let ast_doc = match parse_ast(&ast_text) {
        Ok(parsed) => parsed,
        Err(err) => {
            report.errors.push(err);
            return finish_check_report(report, json);
        }
    };

    report.ast_version = Some(ast_doc.ast_version.clone());
    report.goal = Some(ast_doc.goal.clone());
    report.task_count = Some(ast_doc.tasks.len());

    if let Err(err) = validate_ast(&ast_doc) {
        report.errors.push(err);
        return finish_check_report(report, json);
    }

    report.ok = true;
    finish_check_report(report, json)
}

fn finish_check_report(report: CheckAstReport, json: bool) -> i32 {
    if json {
        let rendered = serde_json::to_string_pretty(&report).unwrap_or_else(|err| {
            format!(
                "{{\"ok\":false,\"errors\":[\"failed to serialize check report: {err}\"]}}"
            )
        });
        println!("{rendered}");
    } else if report.ok {
        println!("ok");
    } else {
        eprintln!("{}", report.errors.join("; "));
    }
    if report.ok { 0 } else { 1 }
}

fn run_trace_skeleton(ast: PathBuf) -> i32 {
    let ast_text = match fs::read_to_string(&ast) {
        Ok(text) => text,
        Err(err) => {
            eprintln!("failed to read AST file '{}': {err}", ast.display());
            return 1;
        }
    };
    let ast_doc = match parse_ast(&ast_text) {
        Ok(parsed) => parsed,
        Err(err) => {
            eprintln!("{err}");
            return 1;
        }
    };
    if let Err(err) = validate_ast(&ast_doc) {
        eprintln!("{err}");
        return 1;
    }
    let trace = build_trace_skeleton(&ast_doc);
    let rendered = match serde_json::to_string_pretty(&trace) {
        Ok(value) => value,
        Err(err) => {
            eprintln!("failed to serialize trace skeleton: {err}");
            return 1;
        }
    };
    println!("{rendered}");
    0
}
