use clap::{Parser, Subcommand};
use missiongraph_rs::{build_trace_skeleton, parse_ast, validate_ast};
use serde::Serialize;
use serde_json::Value;
use std::fs;
use std::io::Write;
use std::path::Path;
use std::path::PathBuf;
use std::process::{Command, Stdio};

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
    /// Execute a single dependency-free task worker from AST (prototype).
    RunTask {
        /// Path to AST JSON file (for example output of `mgl parse`).
        ast: PathBuf,
        /// Task name to execute.
        #[arg(long)]
        task: String,
        /// Base directory used to resolve relative worker paths.
        #[arg(long, default_value = ".")]
        base_dir: PathBuf,
        /// JSON input payload sent to worker stdin.
        #[arg(long, default_value = "{}")]
        input: String,
        /// Emit machine-readable JSON status payload.
        #[arg(long)]
        json: bool,
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

#[derive(Debug, Serialize)]
struct RunTaskReport {
    ok: bool,
    task: String,
    worker: Option<String>,
    worker_path: Option<String>,
    exit_code: Option<i32>,
    status: Option<String>,
    confidence: Option<f64>,
    output: Option<Value>,
    provenance: Option<Value>,
    error: Option<String>,
    stderr: Option<String>,
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
        Commands::RunTask {
            ast,
            task,
            base_dir,
            input,
            json,
        } => run_task(ast, task, base_dir, input, json),
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

fn run_task(ast: PathBuf, task_name: String, base_dir: PathBuf, input: String, json: bool) -> i32 {
    let mut report = RunTaskReport {
        ok: false,
        task: task_name.clone(),
        worker: None,
        worker_path: None,
        exit_code: None,
        status: None,
        confidence: None,
        output: None,
        provenance: None,
        error: None,
        stderr: None,
    };

    let input_payload = match serde_json::from_str::<Value>(&input) {
        Ok(value) => value,
        Err(err) => {
            report.error = Some(format!("invalid --input JSON: {err}"));
            return finish_run_task_report(report, json);
        }
    };

    let ast_text = match fs::read_to_string(&ast) {
        Ok(text) => text,
        Err(err) => {
            report.error = Some(format!("failed to read AST file '{}': {err}", ast.display()));
            return finish_run_task_report(report, json);
        }
    };

    let ast_doc = match parse_ast(&ast_text) {
        Ok(parsed) => parsed,
        Err(err) => {
            report.error = Some(err);
            return finish_run_task_report(report, json);
        }
    };

    if let Err(err) = validate_ast(&ast_doc) {
        report.error = Some(err);
        return finish_run_task_report(report, json);
    }

    let ast_task = match ast_doc.tasks.iter().find(|candidate| candidate.name == task_name) {
        Some(task) => task,
        None => {
            report.error = Some(format!("task '{}' not found in AST", task_name));
            return finish_run_task_report(report, json);
        }
    };
    report.worker = Some(ast_task.worker.clone());

    if !ast_task.after.is_empty() {
        report.error = Some(format!(
            "run-task prototype only supports dependency-free tasks; '{}' depends on: {}",
            task_name,
            ast_task.after.join(", ")
        ));
        return finish_run_task_report(report, json);
    }
    if ast_task.worker.trim().is_empty() {
        report.error = Some(format!("task '{}' has empty worker path", task_name));
        return finish_run_task_report(report, json);
    }

    let worker_path = resolve_worker_path(&base_dir, &ast_task.worker);
    report.worker_path = Some(worker_path.display().to_string());
    if !worker_path.exists() {
        report.error = Some(format!("worker path does not exist: {}", worker_path.display()));
        return finish_run_task_report(report, json);
    }

    let payload_text = match serde_json::to_string(&input_payload) {
        Ok(text) => text,
        Err(err) => {
            report.error = Some(format!("failed to serialize input payload: {err}"));
            return finish_run_task_report(report, json);
        }
    };

    let mut child = match Command::new("python3")
        .arg(&worker_path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(proc) => proc,
        Err(err) => {
            report.error = Some(format!("failed to launch worker: {err}"));
            return finish_run_task_report(report, json);
        }
    };

    if let Some(mut stdin) = child.stdin.take() {
        if let Err(err) = stdin.write_all(payload_text.as_bytes()) {
            report.error = Some(format!("failed to write worker stdin: {err}"));
            return finish_run_task_report(report, json);
        }
    }

    let output = match child.wait_with_output() {
        Ok(result) => result,
        Err(err) => {
            report.error = Some(format!("failed waiting for worker process: {err}"));
            return finish_run_task_report(report, json);
        }
    };

    report.exit_code = output.status.code();
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    if !stderr.is_empty() {
        report.stderr = Some(stderr.clone());
    }
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if stdout.is_empty() {
        report.error = Some("worker returned empty stdout".to_string());
        return finish_run_task_report(report, json);
    }

    let worker_payload = match serde_json::from_str::<Value>(&stdout) {
        Ok(value) => value,
        Err(err) => {
            report.error = Some(format!("worker stdout is not valid JSON: {err}"));
            return finish_run_task_report(report, json);
        }
    };

    report.status = worker_payload
        .get("status")
        .and_then(|value| value.as_str())
        .map(str::to_string);
    report.confidence = worker_payload
        .get("confidence")
        .and_then(|value| value.as_f64());
    report.output = worker_payload.get("output").cloned();
    report.provenance = worker_payload.get("provenance").cloned();
    report.error = worker_payload
        .get("error")
        .and_then(|value| value.as_str())
        .map(str::to_string);

    if !output.status.success() && report.error.is_none() {
        report.error = Some(format!(
            "worker exited non-zero (exit={})",
            report.exit_code
                .map(|code| code.to_string())
                .unwrap_or_else(|| "unknown".to_string())
        ));
    }

    report.ok = output.status.success() && report.status.as_deref() == Some("ok");
    finish_run_task_report(report, json)
}

fn finish_run_task_report(report: RunTaskReport, json: bool) -> i32 {
    if json {
        let rendered = serde_json::to_string_pretty(&report).unwrap_or_else(|err| {
            format!(
                "{{\"ok\":false,\"error\":\"failed to serialize run-task report: {err}\"}}"
            )
        });
        println!("{rendered}");
    } else if report.ok {
        println!("ok");
    } else {
        let message = report
            .error
            .clone()
            .unwrap_or_else(|| "run-task failed".to_string());
        eprintln!("{message}");
    }
    if report.ok { 0 } else { 1 }
}

fn resolve_worker_path(base_dir: &Path, worker: &str) -> PathBuf {
    let worker_path = Path::new(worker);
    if worker_path.is_absolute() {
        return worker_path.to_path_buf();
    }
    base_dir.join(worker_path)
}
