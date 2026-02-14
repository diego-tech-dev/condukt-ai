use clap::{Parser, Subcommand};
use missiongraph_rs::{
    build_dependency_levels, build_trace_skeleton, parse_ast, validate_ast, AstTask,
    TRACE_VERSION,
};
use serde::Serialize;
use serde_json::Value;
use serde_json::json;
use std::fs;
use std::io::Write;
use std::collections::BTreeMap;
use std::path::Path;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};

const ERROR_CODE_RUNTIME_EXECUTION_FAILURE: &str = "RUNTIME_EXECUTION_FAILURE";
const ERROR_CODE_WORKER_OUTPUT_JSON_INVALID: &str = "WORKER_OUTPUT_JSON_INVALID";
const ERROR_CODE_WORKER_EXIT_NONZERO: &str = "WORKER_EXIT_NONZERO";

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
        /// Internal: allow tasks with dependencies.
        #[arg(long, hide = true)]
        allow_deps: bool,
    },
    /// Execute all tasks sequentially in dependency order from AST.
    RunPlan {
        /// Path to AST JSON file (for example output of `mgl parse`).
        ast: PathBuf,
        /// Base directory used to resolve relative worker paths.
        #[arg(long, default_value = ".")]
        base_dir: PathBuf,
        /// Declared capabilities for trace metadata.
        #[arg(long = "capability")]
        capabilities: Vec<String>,
        /// Emit machine-readable JSON trace payload.
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
    error_code: Option<String>,
    provenance: Option<Value>,
    error: Option<String>,
    started_at: Option<String>,
    finished_at: Option<String>,
    stderr: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
struct TraceTaskResult {
    task: String,
    worker: String,
    status: String,
    confidence: f64,
    output: Value,
    error_code: Option<String>,
    error: Option<String>,
    started_at: String,
    finished_at: String,
    provenance: Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    stderr: Option<String>,
}

#[derive(Debug, Serialize)]
struct TraceExecution {
    mode: String,
    max_parallel: i32,
    levels: Vec<Vec<String>>,
}

#[derive(Debug, Serialize)]
struct TraceVerifySummary {
    total: i32,
    passed: i32,
    failed: i32,
    failures: Vec<Value>,
}

#[derive(Debug, Serialize)]
struct RunPlanTrace {
    trace_version: String,
    goal: String,
    status: String,
    started_at: String,
    finished_at: String,
    capabilities: Vec<String>,
    execution: TraceExecution,
    task_order: Vec<String>,
    tasks: Vec<TraceTaskResult>,
    constraints: Vec<Value>,
    verify: Vec<Value>,
    verify_summary: TraceVerifySummary,
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
            allow_deps,
        } => run_task(ast, task, base_dir, input, json, allow_deps),
        Commands::RunPlan {
            ast,
            base_dir,
            capabilities,
            json,
        } => run_plan(ast, base_dir, capabilities, json),
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

fn run_task(
    ast: PathBuf,
    task_name: String,
    base_dir: PathBuf,
    input: String,
    json: bool,
    allow_deps: bool,
) -> i32 {
    let input_payload = match serde_json::from_str::<Value>(&input) {
        Ok(value) => value,
        Err(err) => {
            let mut report = empty_run_task_report(&task_name);
            report.error = Some(format!("invalid --input JSON: {err}"));
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            return finish_run_task_report(report, json);
        }
    };

    let ast_text = match fs::read_to_string(&ast) {
        Ok(text) => text,
        Err(err) => {
            let mut report = empty_run_task_report(&task_name);
            report.error = Some(format!("failed to read AST file '{}': {err}", ast.display()));
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            return finish_run_task_report(report, json);
        }
    };
    let ast_doc = match parse_ast(&ast_text) {
        Ok(parsed) => parsed,
        Err(err) => {
            let mut report = empty_run_task_report(&task_name);
            report.error = Some(err);
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            return finish_run_task_report(report, json);
        }
    };
    if let Err(err) = validate_ast(&ast_doc) {
        let mut report = empty_run_task_report(&task_name);
        report.error = Some(err);
        report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
        return finish_run_task_report(report, json);
    }

    let ast_task = match ast_doc.tasks.iter().find(|candidate| candidate.name == task_name) {
        Some(task) => task,
        None => {
            let mut report = empty_run_task_report(&task_name);
            report.error = Some(format!("task '{}' not found in AST", task_name));
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            return finish_run_task_report(report, json);
        }
    };

    let report = execute_task_from_ast(ast_task, &base_dir, input_payload, allow_deps);
    finish_run_task_report(report, json)
}

fn run_plan(ast: PathBuf, base_dir: PathBuf, capabilities: Vec<String>, json: bool) -> i32 {
    let ast_text = match fs::read_to_string(&ast) {
        Ok(text) => text,
        Err(err) => {
            if json {
                println!(
                    "{}",
                    json!({
                        "trace_version": TRACE_VERSION,
                        "status": "failed",
                        "error": format!("failed to read AST file '{}': {err}", ast.display()),
                    })
                );
            } else {
                eprintln!("failed to read AST file '{}': {err}", ast.display());
            }
            return 1;
        }
    };
    let ast_doc = match parse_ast(&ast_text) {
        Ok(parsed) => parsed,
        Err(err) => {
            if json {
                println!(
                    "{}",
                    json!({
                        "trace_version": TRACE_VERSION,
                        "status": "failed",
                        "error": err,
                    })
                );
            } else {
                eprintln!("{err}");
            }
            return 1;
        }
    };
    if let Err(err) = validate_ast(&ast_doc) {
        if json {
            println!(
                "{}",
                json!({
                    "trace_version": TRACE_VERSION,
                    "status": "failed",
                    "error": err,
                })
            );
        } else {
            eprintln!("{err}");
        }
        return 1;
    }

    let levels = match build_dependency_levels(&ast_doc) {
        Ok(levels) => levels,
        Err(err) => {
            if json {
                println!(
                    "{}",
                    json!({
                        "trace_version": TRACE_VERSION,
                        "status": "failed",
                        "error": err,
                    })
                );
            } else {
                eprintln!("{err}");
            }
            return 1;
        }
    };
    let task_order = levels
        .iter()
        .flat_map(|level| level.iter().cloned())
        .collect::<Vec<_>>();
    let task_by_name = ast_doc
        .tasks
        .iter()
        .map(|task| (task.name.clone(), task))
        .collect::<BTreeMap<String, &AstTask>>();

    let started_at = now_timestamp();
    let mut task_values: BTreeMap<String, Value> = BTreeMap::new();
    let mut tasks: Vec<TraceTaskResult> = vec![];

    for task_name in &task_order {
        let task = task_by_name
            .get(task_name)
            .expect("validated task order should resolve to task definitions");

        let mut dependencies = serde_json::Map::new();
        for dep in &task.after {
            if let Some(value) = task_values.get(dep) {
                dependencies.insert(dep.clone(), value.clone());
            }
        }

        let payload = json!({
            "task": task.name,
            "goal": ast_doc.goal,
            "constraints": [],
            "dependencies": dependencies,
            "variables": {},
        });

        let report = execute_task_from_ast(task, &base_dir, payload, true);
        let trace_task = report_to_trace_task(&report);
        task_values.insert(task.name.clone(), trace_task_to_value(&trace_task));
        let failed = trace_task.status != "ok";
        tasks.push(trace_task);
        if failed {
            break;
        }
    }

    let trace = RunPlanTrace {
        trace_version: TRACE_VERSION.to_string(),
        goal: ast_doc.goal,
        status: if tasks.len() == task_order.len() && tasks.iter().all(|t| t.status == "ok") {
            "ok".to_string()
        } else {
            "failed".to_string()
        },
        started_at,
        finished_at: now_timestamp(),
        capabilities: {
            let mut out = capabilities;
            out.sort();
            out.dedup();
            out
        },
        execution: TraceExecution {
            mode: "sequential".to_string(),
            max_parallel: 1,
            levels,
        },
        task_order,
        tasks,
        constraints: vec![],
        verify: vec![],
        verify_summary: TraceVerifySummary {
            total: 0,
            passed: 0,
            failed: 0,
            failures: vec![],
        },
    };

    if json {
        let rendered = serde_json::to_string_pretty(&trace).unwrap_or_else(|err| {
            format!(
                "{{\"trace_version\":\"{}\",\"status\":\"failed\",\"error\":\"failed to serialize run-plan trace: {}\"}}",
                TRACE_VERSION, err
            )
        });
        println!("{rendered}");
    } else {
        println!("{}", trace.status);
    }
    if trace.status == "ok" { 0 } else { 1 }
}

fn empty_run_task_report(task_name: &str) -> RunTaskReport {
    RunTaskReport {
        ok: false,
        task: task_name.to_string(),
        worker: None,
        worker_path: None,
        exit_code: None,
        status: None,
        confidence: None,
        output: None,
        error_code: None,
        provenance: None,
        error: None,
        started_at: None,
        finished_at: None,
        stderr: None,
    }
}

fn execute_task_from_ast(
    ast_task: &AstTask,
    base_dir: &Path,
    input_payload: Value,
    allow_deps: bool,
) -> RunTaskReport {
    let mut report = empty_run_task_report(&ast_task.name);
    report.worker = Some(ast_task.worker.clone());

    if !allow_deps && !ast_task.after.is_empty() {
        report.error = Some(format!(
            "run-task prototype only supports dependency-free tasks; '{}' depends on: {}",
            ast_task.name,
            ast_task.after.join(", ")
        ));
        report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
        return report;
    }
    if ast_task.worker.trim().is_empty() {
        report.error = Some(format!("task '{}' has empty worker path", ast_task.name));
        report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
        return report;
    }

    let worker_path = resolve_worker_path(base_dir, &ast_task.worker);
    report.worker_path = Some(worker_path.display().to_string());
    if !worker_path.exists() {
        report.error = Some(format!("worker path does not exist: {}", worker_path.display()));
        report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
        return report;
    }

    let payload_text = match serde_json::to_string(&input_payload) {
        Ok(text) => text,
        Err(err) => {
            report.error = Some(format!("failed to serialize input payload: {err}"));
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            return report;
        }
    };

    report.started_at = Some(now_timestamp());

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
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            report.finished_at = Some(now_timestamp());
            return report;
        }
    };

    if let Some(mut stdin) = child.stdin.take() {
        if let Err(err) = stdin.write_all(payload_text.as_bytes()) {
            report.error = Some(format!("failed to write worker stdin: {err}"));
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            report.finished_at = Some(now_timestamp());
            return report;
        }
    }

    let output = match child.wait_with_output() {
        Ok(result) => result,
        Err(err) => {
            report.error = Some(format!("failed waiting for worker process: {err}"));
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            report.finished_at = Some(now_timestamp());
            return report;
        }
    };
    report.finished_at = Some(now_timestamp());
    report.exit_code = output.status.code();

    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    if !stderr.is_empty() {
        report.stderr = Some(stderr);
    }
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if stdout.is_empty() {
        report.error = Some("worker returned empty stdout".to_string());
        report.error_code = Some(if !output.status.success() {
            ERROR_CODE_WORKER_EXIT_NONZERO.to_string()
        } else {
            ERROR_CODE_WORKER_OUTPUT_JSON_INVALID.to_string()
        });
        report.status = Some("error".to_string());
        report.confidence = Some(0.0);
        report.output = Some(Value::Object(serde_json::Map::new()));
        report.provenance = Some(default_provenance(
            &worker_path,
            report.exit_code,
            &ast_task.worker,
            None,
        ));
        return finalize_run_task_report(report);
    }

    let worker_payload = match serde_json::from_str::<Value>(&stdout) {
        Ok(value) => value,
        Err(err) => {
            report.error = Some(format!("worker stdout is not valid JSON: {err}"));
            report.error_code = Some(ERROR_CODE_WORKER_OUTPUT_JSON_INVALID.to_string());
            report.status = Some("error".to_string());
            report.confidence = Some(0.0);
            report.output = Some(Value::Object(serde_json::Map::new()));
            report.provenance = Some(default_provenance(
                &worker_path,
                report.exit_code,
                &ast_task.worker,
                None,
            ));
            return finalize_run_task_report(report);
        }
    };
    let worker_object = match worker_payload.as_object() {
        Some(obj) => obj,
        None => {
            report.error = Some("worker output must be a JSON object".to_string());
            report.error_code = Some(ERROR_CODE_WORKER_OUTPUT_JSON_INVALID.to_string());
            report.status = Some("error".to_string());
            report.confidence = Some(0.0);
            report.output = Some(Value::Object(serde_json::Map::new()));
            report.provenance = Some(default_provenance(
                &worker_path,
                report.exit_code,
                &ast_task.worker,
                None,
            ));
            return finalize_run_task_report(report);
        }
    };

    report.status = worker_object
        .get("status")
        .and_then(|value| value.as_str())
        .map(str::to_string);
    report.confidence = worker_object
        .get("confidence")
        .and_then(|value| value.as_f64());
    report.error = worker_object
        .get("error")
        .and_then(|value| value.as_str())
        .map(str::to_string);
    report.error_code = worker_object
        .get("error_code")
        .and_then(|value| value.as_str())
        .map(str::to_string);

    let output_value = worker_object
        .get("output")
        .cloned()
        .unwrap_or_else(|| Value::Object(serde_json::Map::new()));
    report.output = Some(match output_value {
        Value::Object(_) => output_value,
        other => {
            let mut wrapped = serde_json::Map::new();
            wrapped.insert("value".to_string(), other);
            Value::Object(wrapped)
        }
    });

    report.provenance = Some(default_provenance(
        &worker_path,
        report.exit_code,
        &ast_task.worker,
        worker_object.get("provenance").cloned(),
    ));

    finalize_run_task_report(report)
}

fn finalize_run_task_report(mut report: RunTaskReport) -> RunTaskReport {
    if report.status.is_none() {
        report.status = Some(if report.exit_code == Some(0) {
            "ok".to_string()
        } else {
            "error".to_string()
        });
    }
    if report.confidence.is_none() {
        report.confidence = Some(if report.status.as_deref() == Some("ok") {
            0.5
        } else {
            0.0
        });
    }

    if report.exit_code != Some(0) {
        if report.status.as_deref() == Some("ok") {
            report.status = Some("error".to_string());
        }
        if report.error_code.is_none() {
            report.error_code = Some(ERROR_CODE_WORKER_EXIT_NONZERO.to_string());
        }
        if report.error.is_none() {
            report.error = Some(format!(
                "worker exited with return code {}",
                report
                    .exit_code
                    .map(|code| code.to_string())
                    .unwrap_or_else(|| "unknown".to_string())
            ));
        }
    }

    report.ok = report.status.as_deref() == Some("ok");
    report
}

fn report_to_trace_task(report: &RunTaskReport) -> TraceTaskResult {
    TraceTaskResult {
        task: report.task.clone(),
        worker: report.worker.clone().unwrap_or_default(),
        status: report
            .status
            .clone()
            .unwrap_or_else(|| "error".to_string()),
        confidence: report.confidence.unwrap_or(0.0),
        output: report
            .output
            .clone()
            .unwrap_or_else(|| Value::Object(serde_json::Map::new())),
        error_code: report.error_code.clone(),
        error: report.error.clone(),
        started_at: report
            .started_at
            .clone()
            .unwrap_or_else(now_timestamp),
        finished_at: report
            .finished_at
            .clone()
            .unwrap_or_else(now_timestamp),
        provenance: report
            .provenance
            .clone()
            .unwrap_or_else(|| Value::Object(serde_json::Map::new())),
        stderr: report.stderr.clone(),
    }
}

fn trace_task_to_value(task: &TraceTaskResult) -> Value {
    serde_json::to_value(task).unwrap_or_else(|_| Value::Object(serde_json::Map::new()))
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

fn now_timestamp() -> String {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default();
    format!("{:.3}", now.as_secs_f64())
}

fn default_provenance(
    worker_path: &Path,
    exit_code: Option<i32>,
    worker_ref: &str,
    worker_provenance: Option<Value>,
) -> Value {
    let mut provenance = serde_json::Map::new();
    provenance.insert(
        "worker".to_string(),
        Value::String(worker_path.display().to_string()),
    );
    provenance.insert(
        "command".to_string(),
        Value::String(format!("python3 {}", worker_path.display())),
    );
    provenance.insert(
        "worker_ref".to_string(),
        Value::String(worker_ref.to_string()),
    );
    provenance.insert(
        "return_code".to_string(),
        match exit_code {
            Some(code) => Value::from(code),
            None => Value::Null,
        },
    );

    if let Some(Value::Object(custom)) = worker_provenance {
        for (key, value) in custom {
            provenance.insert(key, value);
        }
    }

    Value::Object(provenance)
}
