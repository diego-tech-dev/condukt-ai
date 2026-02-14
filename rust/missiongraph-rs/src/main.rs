use clap::{Parser, Subcommand};
use missiongraph_rs::{
    build_dependency_levels, build_trace_skeleton, parse_ast, validate_ast, AstConstraint,
    AstTask, AstVerify, TRACE_VERSION,
};
use serde::Serialize;
use serde_json::json;
use serde_json::Value;
use std::collections::BTreeMap;
use std::fs;
use std::io::Write;
use std::path::Path;
use std::path::PathBuf;
use std::process::{Child, Command, Output, Stdio};
use std::thread::sleep;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

const ERROR_CODE_RUNTIME_EXECUTION_FAILURE: &str = "RUNTIME_EXECUTION_FAILURE";
const ERROR_CODE_WORKER_OUTPUT_JSON_INVALID: &str = "WORKER_OUTPUT_JSON_INVALID";
const ERROR_CODE_WORKER_EXIT_NONZERO: &str = "WORKER_EXIT_NONZERO";
const ERROR_CODE_WORKER_TIMEOUT: &str = "WORKER_TIMEOUT";

#[derive(Debug, Clone)]
struct TaskPolicy {
    timeout_seconds: Option<f64>,
    retries: u32,
    retry_if: String,
    backoff_seconds: f64,
    jitter_seconds: f64,
}

impl TaskPolicy {
    fn from_task(task: &AstTask) -> Self {
        Self {
            timeout_seconds: task.timeout_seconds,
            retries: task.retries.unwrap_or(0),
            retry_if: task
                .retry_if
                .clone()
                .unwrap_or_else(|| "error".to_string()),
            backoff_seconds: task.backoff_seconds.unwrap_or(0.0),
            jitter_seconds: task.jitter_seconds.unwrap_or(0.0),
        }
    }

    fn max_attempts(&self) -> u32 {
        self.retries.saturating_add(1)
    }
}

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
    let mut shared_context: serde_json::Map<String, Value> = serde_json::Map::new();
    let constraint_values = ast_doc
        .constraints
        .iter()
        .map(constraint_to_value)
        .collect::<Vec<_>>();
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
            "constraints": constraint_values.clone(),
            "dependencies": dependencies,
            "variables": shared_context.clone(),
        });

        let report = execute_task_from_ast(task, &base_dir, payload, true);
        let trace_task = report_to_trace_task(&report);
        task_values.insert(task.name.clone(), trace_task_to_value(&trace_task));
        if trace_task.status == "ok" {
            if let Value::Object(output_map) = &trace_task.output {
                for (key, value) in output_map {
                    if !task_values.contains_key(key) {
                        shared_context.insert(key.clone(), value.clone());
                    }
                }
            }
        }
        let failed = trace_task.status != "ok";
        tasks.push(trace_task);
        if failed {
            break;
        }
    }

    let constraints_report = evaluate_constraints(&ast_doc.constraints, &shared_context);
    let verify_report = evaluate_verify(&ast_doc.verify, &task_values, &shared_context);
    let verify_summary = summarize_verify(&verify_report);
    let task_status_ok = tasks.iter().all(|task| task.status == "ok");
    let constraints_ok = constraints_report
        .iter()
        .all(|item| !report_value_is_false(item, "passed"));
    let verify_ok = verify_summary.failed == 0;
    let overall_ok = task_status_ok && constraints_ok && verify_ok;

    let trace = RunPlanTrace {
        trace_version: TRACE_VERSION.to_string(),
        goal: ast_doc.goal,
        status: if overall_ok {
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
        constraints: constraints_report,
        verify: verify_report,
        verify_summary,
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

fn constraint_to_value(constraint: &AstConstraint) -> Value {
    json!({
        "key": constraint.key.clone(),
        "op": constraint.op.clone(),
        "value": constraint.value.clone(),
        "line": constraint.line,
    })
}

fn constraint_expression(constraint: &AstConstraint) -> String {
    let value_text =
        serde_json::to_string(&constraint.value).unwrap_or_else(|_| "null".to_string());
    format!("{} {} {}", constraint.key, constraint.op, value_text)
}

fn evaluate_constraints(
    constraints: &[AstConstraint],
    context: &serde_json::Map<String, Value>,
) -> Vec<Value> {
    constraints
        .iter()
        .map(|constraint| {
            let expression = constraint_expression(constraint);
            let left_value = match resolve_path(context, &constraint.key) {
                Some(value) => value,
                None => {
                    return json!({
                        "line": constraint.line,
                        "expression": expression,
                        "passed": Value::Null,
                        "reason": format!("unresolved key: {}", constraint.key),
                    });
                }
            };

            match compare_values(&left_value, &constraint.value, constraint.op.as_str()) {
                Ok(passed) => json!({
                    "line": constraint.line,
                    "expression": expression,
                    "passed": passed,
                }),
                Err(reason) => json!({
                    "line": constraint.line,
                    "expression": expression,
                    "passed": false,
                    "reason": reason,
                }),
            }
        })
        .collect()
}

fn evaluate_verify(
    checks: &[AstVerify],
    task_values: &BTreeMap<String, Value>,
    context: &serde_json::Map<String, Value>,
) -> Vec<Value> {
    let mut eval_context = context.clone();
    for (task, value) in task_values {
        eval_context.insert(task.clone(), value.clone());
    }

    checks
        .iter()
        .map(|check| match eval_boolean_expression(&check.expression, &eval_context) {
            Ok(passed) => json!({
                "line": check.line,
                "expression": check.expression,
                "passed": passed,
            }),
            Err(reason) => json!({
                "line": check.line,
                "expression": check.expression,
                "passed": false,
                "reason": reason,
            }),
        })
        .collect()
}

fn summarize_verify(report: &[Value]) -> TraceVerifySummary {
    let failures = report
        .iter()
        .filter(|item| report_value_is_false(item, "passed"))
        .map(|item| {
            let line = item
                .as_object()
                .and_then(|obj| obj.get("line"))
                .and_then(|value| value.as_u64())
                .unwrap_or(0);
            let expression = item
                .as_object()
                .and_then(|obj| obj.get("expression"))
                .and_then(|value| value.as_str())
                .unwrap_or("");
            let reason = item
                .as_object()
                .and_then(|obj| obj.get("reason"))
                .cloned()
                .unwrap_or(Value::Null);
            json!({
                "line": line,
                "expression": expression,
                "reason": reason,
            })
        })
        .collect::<Vec<_>>();

    let total = report.len() as i32;
    let failed = failures.len() as i32;
    TraceVerifySummary {
        total,
        passed: total - failed,
        failed,
        failures,
    }
}

fn report_value_is_false(item: &Value, key: &str) -> bool {
    item.as_object()
        .and_then(|obj| obj.get(key))
        .and_then(|value| value.as_bool())
        == Some(false)
}

fn eval_boolean_expression(
    expression: &str,
    context: &serde_json::Map<String, Value>,
) -> Result<bool, String> {
    let expr = expression.trim();
    if expr.is_empty() {
        return Err("empty expression".to_string());
    }

    if let Some((index, op)) = find_binary_operator(expr) {
        let left = expr[..index].trim();
        let right = expr[index + op.len()..].trim();
        if left.is_empty() || right.is_empty() {
            return Err(format!("invalid binary expression: {expr}"));
        }
        let left_value = resolve_operand(left, context)?;
        let right_value = resolve_operand(right, context)?;
        return compare_values(&left_value, &right_value, op);
    }

    let value = resolve_operand(expr, context)?;
    value
        .as_bool()
        .ok_or_else(|| format!("expression did not resolve to bool: {expr}"))
}

fn find_binary_operator(expression: &str) -> Option<(usize, &'static str)> {
    let bytes = expression.as_bytes();
    let mut in_string = false;
    let mut escaped = false;
    let mut index = 0usize;

    while index < bytes.len() {
        let byte = bytes[index];

        if in_string {
            if escaped {
                escaped = false;
                index += 1;
                continue;
            }
            if byte == b'\\' {
                escaped = true;
                index += 1;
                continue;
            }
            if byte == b'"' {
                in_string = false;
            }
            index += 1;
            continue;
        }

        if byte == b'"' {
            in_string = true;
            index += 1;
            continue;
        }

        for op in ["==", "!=", ">=", "<="] {
            if expression[index..].starts_with(op) {
                return Some((index, op));
            }
        }
        if byte == b'>' {
            return Some((index, ">"));
        }
        if byte == b'<' {
            return Some((index, "<"));
        }
        index += 1;
    }

    None
}

fn resolve_operand(
    token: &str,
    context: &serde_json::Map<String, Value>,
) -> Result<Value, String> {
    if let Ok(value) = serde_json::from_str::<Value>(token) {
        return Ok(value);
    }
    if let Some(value) = resolve_path(context, token) {
        return Ok(value);
    }
    Err(format!("unresolved identifier: {token}"))
}

fn resolve_path(context: &serde_json::Map<String, Value>, path: &str) -> Option<Value> {
    let mut parts = path.split('.');
    let first = parts.next()?;
    let mut current = context.get(first)?;
    for part in parts {
        let object = current.as_object()?;
        current = object.get(part)?;
    }
    Some(current.clone())
}

fn compare_values(left: &Value, right: &Value, op: &str) -> Result<bool, String> {
    match op {
        "==" => Ok(left == right),
        "!=" => Ok(left != right),
        "<" | "<=" | ">" | ">=" => {
            if let (Some(left_num), Some(right_num)) = (left.as_f64(), right.as_f64()) {
                return Ok(match op {
                    "<" => left_num < right_num,
                    "<=" => left_num <= right_num,
                    ">" => left_num > right_num,
                    ">=" => left_num >= right_num,
                    _ => false,
                });
            }
            if let (Some(left_str), Some(right_str)) = (left.as_str(), right.as_str()) {
                return Ok(match op {
                    "<" => left_str < right_str,
                    "<=" => left_str <= right_str,
                    ">" => left_str > right_str,
                    ">=" => left_str >= right_str,
                    _ => false,
                });
            }
            Err(format!(
                "unsupported comparison: {} {} {}",
                value_type_name(left),
                op,
                value_type_name(right)
            ))
        }
        _ => Err(format!("unsupported operator: {op}")),
    }
}

fn value_type_name(value: &Value) -> &'static str {
    match value {
        Value::Null => "null",
        Value::Bool(_) => "bool",
        Value::Number(_) => "number",
        Value::String(_) => "string",
        Value::Array(_) => "array",
        Value::Object(_) => "object",
    }
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
    let policy = TaskPolicy::from_task(ast_task);
    let max_attempts = policy.max_attempts();
    let mut attempt_history: Vec<Value> = vec![];
    let mut last_report: Option<RunTaskReport> = None;

    for attempt in 1..=max_attempts {
        let attempt_report = execute_task_attempt(
            ast_task,
            &worker_path,
            &payload_text,
            &policy,
            attempt,
            max_attempts,
        );

        attempt_history.push(json!({
            "attempt": attempt,
            "status": attempt_report.status,
            "error_code": attempt_report.error_code,
            "error": attempt_report.error,
            "started_at": attempt_report.started_at,
            "finished_at": attempt_report.finished_at,
        }));

        let is_ok = attempt_report.status.as_deref() == Some("ok");
        let should_retry_attempt = should_retry(&policy, &attempt_report);
        let is_last_attempt = attempt == max_attempts;
        last_report = Some(attempt_report);
        if is_ok || !should_retry_attempt || is_last_attempt {
            break;
        }

        let delay_seconds = retry_delay_seconds(
            policy.backoff_seconds,
            attempt,
            policy.jitter_seconds,
        );
        if delay_seconds > 0.0 {
            sleep(Duration::from_secs_f64(delay_seconds));
        }
    }

    let mut final_report = last_report.unwrap_or(report);
    if max_attempts > 1 {
        let mut provenance = match final_report.provenance.take() {
            Some(Value::Object(map)) => map,
            _ => serde_json::Map::new(),
        };
        provenance.insert("attempts".to_string(), Value::Array(attempt_history));
        final_report.provenance = Some(Value::Object(provenance));
    }
    final_report
}

fn execute_task_attempt(
    ast_task: &AstTask,
    worker_path: &Path,
    payload_text: &str,
    policy: &TaskPolicy,
    attempt: u32,
    max_attempts: u32,
) -> RunTaskReport {
    let mut report = empty_run_task_report(&ast_task.name);
    report.worker = Some(ast_task.worker.clone());
    report.worker_path = Some(worker_path.display().to_string());
    report.started_at = Some(now_timestamp());

    let mut child = match Command::new("python3")
        .arg(worker_path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(proc) => proc,
        Err(err) => {
            report.error = Some(format!("failed to launch worker: {err}"));
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            report.status = Some("error".to_string());
            report.confidence = Some(0.0);
            report.output = Some(Value::Object(serde_json::Map::new()));
            report.finished_at = Some(now_timestamp());
            report.provenance = Some(default_provenance(
                worker_path,
                None,
                &ast_task.worker,
                policy,
                attempt,
                max_attempts,
                None,
            ));
            return finalize_run_task_report(report);
        }
    };

    if let Some(mut stdin) = child.stdin.take() {
        if let Err(err) = stdin.write_all(payload_text.as_bytes()) {
            report.error = Some(format!("failed to write worker stdin: {err}"));
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            report.status = Some("error".to_string());
            report.confidence = Some(0.0);
            report.output = Some(Value::Object(serde_json::Map::new()));
            report.finished_at = Some(now_timestamp());
            report.provenance = Some(default_provenance(
                worker_path,
                None,
                &ast_task.worker,
                policy,
                attempt,
                max_attempts,
                None,
            ));
            return finalize_run_task_report(report);
        }
    }

    let (output, timed_out) = match wait_with_timeout(child, policy.timeout_seconds) {
        Ok(result) => result,
        Err(err) => {
            report.error = Some(format!("failed waiting for worker process: {err}"));
            report.error_code = Some(ERROR_CODE_RUNTIME_EXECUTION_FAILURE.to_string());
            report.status = Some("error".to_string());
            report.confidence = Some(0.0);
            report.output = Some(Value::Object(serde_json::Map::new()));
            report.finished_at = Some(now_timestamp());
            report.provenance = Some(default_provenance(
                worker_path,
                None,
                &ast_task.worker,
                policy,
                attempt,
                max_attempts,
                None,
            ));
            return finalize_run_task_report(report);
        }
    };
    report.finished_at = Some(now_timestamp());
    report.exit_code = if timed_out { None } else { output.status.code() };

    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    if !stderr.is_empty() {
        report.stderr = Some(stderr);
    }
    if timed_out {
        report.status = Some("error".to_string());
        report.confidence = Some(0.0);
        report.output = Some(Value::Object(serde_json::Map::new()));
        report.error_code = Some(ERROR_CODE_WORKER_TIMEOUT.to_string());
        report.error = Some(format!(
            "worker timed out after {}s",
            format_seconds(policy.timeout_seconds.unwrap_or(0.0))
        ));
        report.provenance = Some(default_provenance(
            worker_path,
            None,
            &ast_task.worker,
            policy,
            attempt,
            max_attempts,
            None,
        ));
        return finalize_run_task_report(report);
    }

    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let mut worker_provenance: Option<Value> = None;
    if stdout.is_empty() {
        report.status = Some(if report.exit_code == Some(0) {
            "ok".to_string()
        } else {
            "error".to_string()
        });
        report.confidence = Some(if report.exit_code == Some(0) { 0.5 } else { 0.0 });
        report.output = Some(Value::Object(serde_json::Map::new()));
    } else {
        let worker_payload = match serde_json::from_str::<Value>(&stdout) {
            Ok(value) => value,
            Err(err) => {
                report.error = Some(format!("worker output is not valid JSON: {err}"));
                report.error_code = Some(ERROR_CODE_WORKER_OUTPUT_JSON_INVALID.to_string());
                report.status = Some("error".to_string());
                report.confidence = Some(0.0);
                report.output = Some(Value::Object(serde_json::Map::new()));
                report.provenance = Some(default_provenance(
                    worker_path,
                    report.exit_code,
                    &ast_task.worker,
                    policy,
                    attempt,
                    max_attempts,
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
                    worker_path,
                    report.exit_code,
                    &ast_task.worker,
                    policy,
                    attempt,
                    max_attempts,
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
        worker_provenance = worker_object.get("provenance").cloned();
    }

    report.provenance = Some(default_provenance(
        worker_path,
        report.exit_code,
        &ast_task.worker,
        policy,
        attempt,
        max_attempts,
        worker_provenance,
    ));

    finalize_run_task_report(report)
}

fn wait_with_timeout(mut child: Child, timeout_seconds: Option<f64>) -> Result<(Output, bool), String> {
    let timeout = timeout_seconds
        .filter(|seconds| *seconds > 0.0)
        .map(Duration::from_secs_f64);
    if let Some(limit) = timeout {
        let start = Instant::now();
        loop {
            match child.try_wait() {
                Ok(Some(_)) => {
                    let output = child
                        .wait_with_output()
                        .map_err(|err| format!("failed collecting worker output: {err}"))?;
                    return Ok((output, false));
                }
                Ok(None) => {
                    if start.elapsed() >= limit {
                        let _ = child.kill();
                        let output = child
                            .wait_with_output()
                            .map_err(|err| format!("failed collecting timed-out worker output: {err}"))?;
                        return Ok((output, true));
                    }
                    sleep(Duration::from_millis(10));
                }
                Err(err) => {
                    return Err(format!("failed while polling worker status: {err}"));
                }
            }
        }
    }

    let output = child
        .wait_with_output()
        .map_err(|err| format!("failed waiting for worker process: {err}"))?;
    Ok((output, false))
}

fn retry_delay_seconds(backoff_seconds: f64, attempt: u32, jitter_seconds: f64) -> f64 {
    let mut base = 0.0;
    if backoff_seconds > 0.0 {
        base = backoff_seconds * f64::from(2u32.saturating_pow(attempt.saturating_sub(1)));
    }

    let mut jitter = 0.0;
    if jitter_seconds > 0.0 {
        jitter = random_jitter_fraction() * jitter_seconds;
    }
    base + jitter
}

fn random_jitter_fraction() -> f64 {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .subsec_nanos();
    f64::from(nanos) / 1_000_000_000.0
}

fn should_retry(policy: &TaskPolicy, report: &RunTaskReport) -> bool {
    if policy.retries == 0 {
        return false;
    }
    if report.status.as_deref() == Some("ok") {
        return false;
    }

    let error_code = report.error_code.as_deref();
    match policy.retry_if.as_str() {
        "error" => true,
        "timeout" => error_code == Some(ERROR_CODE_WORKER_TIMEOUT),
        "worker_failure" => matches!(
            error_code,
            Some(
                ERROR_CODE_WORKER_TIMEOUT
                    | ERROR_CODE_WORKER_EXIT_NONZERO
                    | ERROR_CODE_WORKER_OUTPUT_JSON_INVALID
                    | ERROR_CODE_RUNTIME_EXECUTION_FAILURE
            )
        ),
        _ => false,
    }
}

fn format_seconds(seconds: f64) -> String {
    let mut text = format!("{seconds}");
    if text.contains('.') {
        while text.ends_with('0') {
            text.pop();
        }
        if text.ends_with('.') {
            text.pop();
        }
    }
    text
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

    if report.exit_code != Some(0) && report.status.as_deref() == Some("ok") {
        let exit_label = report
            .exit_code
            .map(|code| code.to_string())
            .unwrap_or_else(|| "unknown".to_string());
        report.status = Some("error".to_string());
        report.error_code = Some(ERROR_CODE_WORKER_EXIT_NONZERO.to_string());
        report.error = Some(merge_error(
            report.error.as_deref(),
            &format!("worker exited with return code {exit_label}"),
        ));
    }

    report.ok = report.status.as_deref() == Some("ok");
    report
}

fn merge_error(existing: Option<&str>, new_message: &str) -> String {
    match existing {
        Some(value) if !value.trim().is_empty() => format!("{value}; {new_message}"),
        _ => new_message.to_string(),
    }
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
    policy: &TaskPolicy,
    attempt: u32,
    max_attempts: u32,
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
    if max_attempts > 1 {
        provenance.insert("attempt".to_string(), Value::from(attempt));
        provenance.insert("max_attempts".to_string(), Value::from(max_attempts));
    }
    if let Some(timeout_seconds) = policy.timeout_seconds {
        provenance.insert("timeout_seconds".to_string(), Value::from(timeout_seconds));
    }
    if policy.retries > 0 {
        provenance.insert("retries".to_string(), Value::from(policy.retries));
    }
    if policy.retry_if != "error" {
        provenance.insert("retry_if".to_string(), Value::String(policy.retry_if.clone()));
    }
    if policy.backoff_seconds > 0.0 {
        provenance.insert(
            "backoff_seconds".to_string(),
            Value::from(policy.backoff_seconds),
        );
    }
    if policy.jitter_seconds > 0.0 {
        provenance.insert("jitter_seconds".to_string(), Value::from(policy.jitter_seconds));
    }

    if let Some(Value::Object(custom)) = worker_provenance {
        for (key, value) in custom {
            provenance.insert(key, value);
        }
    }

    Value::Object(provenance)
}
