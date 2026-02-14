use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};

pub const AST_VERSION: &str = "1.1";
pub const TRACE_VERSION: &str = "1.1";

#[derive(Debug, Deserialize)]
pub struct Ast {
    pub ast_version: String,
    pub goal: String,
    pub tasks: Vec<AstTask>,
}

#[derive(Debug, Deserialize)]
pub struct AstTask {
    pub name: String,
    #[serde(default)]
    pub worker: String,
    #[serde(default)]
    pub after: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct Trace {
    pub trace_version: String,
    pub goal: String,
    pub status: String,
    pub started_at: String,
    pub finished_at: String,
    pub capabilities: Vec<String>,
    pub execution: ExecutionInfo,
    pub task_order: Vec<String>,
    pub tasks: Vec<Value>,
    pub constraints: Vec<Value>,
    pub verify: Vec<Value>,
    pub verify_summary: VerifySummary,
}

#[derive(Debug, Serialize)]
pub struct ExecutionInfo {
    pub mode: String,
    pub max_parallel: i32,
    pub levels: Vec<Vec<String>>,
}

#[derive(Debug, Serialize)]
pub struct VerifySummary {
    pub total: i32,
    pub passed: i32,
    pub failed: i32,
    pub failures: Vec<Value>,
}

pub fn parse_ast(text: &str) -> Result<Ast, String> {
    serde_json::from_str::<Ast>(text).map_err(|err| format!("invalid AST JSON: {err}"))
}

pub fn validate_ast(ast: &Ast) -> Result<(), String> {
    if ast.ast_version != AST_VERSION {
        return Err(format!(
            "unsupported ast_version '{}', expected '{}'",
            ast.ast_version, AST_VERSION
        ));
    }

    build_dependency_levels(ast)?;
    Ok(())
}

pub fn build_trace_skeleton(ast: &Ast) -> Trace {
    let fallback_order = ast.tasks.iter().map(|task| task.name.clone()).collect::<Vec<_>>();
    let fallback_levels = if fallback_order.is_empty() {
        vec![]
    } else {
        vec![fallback_order.clone()]
    };

    let levels = build_dependency_levels(ast).unwrap_or(fallback_levels);
    let task_order = levels
        .iter()
        .flat_map(|level| level.iter().cloned())
        .collect::<Vec<_>>();
    let max_parallel = levels.iter().map(|level| level.len()).max().unwrap_or(1);
    let mode = if levels.iter().any(|level| level.len() > 1) {
        "parallel"
    } else {
        "sequential"
    };

    Trace {
        trace_version: TRACE_VERSION.to_string(),
        goal: ast.goal.clone(),
        status: "failed".to_string(),
        started_at: "<ts>".to_string(),
        finished_at: "<ts>".to_string(),
        capabilities: vec![],
        execution: ExecutionInfo {
            mode: mode.to_string(),
            max_parallel: max_parallel as i32,
            levels,
        },
        task_order,
        tasks: vec![],
        constraints: vec![],
        verify: vec![],
        verify_summary: VerifySummary {
            total: 0,
            passed: 0,
            failed: 0,
            failures: vec![],
        },
    }
}

fn build_dependency_levels(ast: &Ast) -> Result<Vec<Vec<String>>, String> {
    let mut seen = BTreeSet::new();
    for task in &ast.tasks {
        if !seen.insert(task.name.clone()) {
            return Err(format!("duplicate task name '{}'", task.name));
        }
    }

    let mut adjacency: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut in_degree: BTreeMap<String, usize> = BTreeMap::new();
    let mut position: BTreeMap<String, usize> = BTreeMap::new();
    for task in &ast.tasks {
        adjacency.insert(task.name.clone(), vec![]);
        in_degree.insert(task.name.clone(), 0);
    }
    for (idx, task) in ast.tasks.iter().enumerate() {
        position.insert(task.name.clone(), idx);
    }

    for task in &ast.tasks {
        for dep in &task.after {
            if !adjacency.contains_key(dep) {
                return Err(format!(
                    "task '{}' depends on unknown task '{}'",
                    task.name, dep
                ));
            }
            adjacency
                .get_mut(dep)
                .expect("dependency must have adjacency entry")
                .push(task.name.clone());
            *in_degree
                .get_mut(&task.name)
                .expect("task must have in-degree entry") += 1;
        }
    }

    for children in adjacency.values_mut() {
        children.sort_by_key(|name| position.get(name).copied().unwrap_or(usize::MAX));
    }

    let mut ready = Vec::new();
    for task in &ast.tasks {
        if in_degree.get(&task.name) == Some(&0) {
            ready.push(task.name.clone());
        }
    }

    let mut levels: Vec<Vec<String>> = vec![];
    let mut seen_count = 0usize;
    while !ready.is_empty() {
        let current_level = ready;
        seen_count += current_level.len();
        levels.push(current_level.clone());

        let mut next_ready: Vec<String> = vec![];
        for current in &current_level {
            if let Some(children) = adjacency.get(current) {
                for child in children {
                    let degree = in_degree
                        .get_mut(child)
                        .expect("child must have in-degree entry");
                    *degree -= 1;
                    if *degree == 0 {
                        next_ready.push(child.clone());
                    }
                }
            }
        }
        ready = next_ready;
    }

    if seen_count != ast.tasks.len() {
        let unresolved = ast
            .tasks
            .iter()
            .filter(|task| in_degree.get(&task.name).copied().unwrap_or(0) > 0)
            .map(|task| task.name.clone())
            .collect::<Vec<_>>();
        return Err(format!("cycle detected in plan: {}", unresolved.join(", ")));
    }

    Ok(levels)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_golden_ast() {
        let ast_text = include_str!("../../../tests/golden/ship_release.ast.json");
        let ast = parse_ast(ast_text).expect("golden AST should parse");
        validate_ast(&ast).expect("golden AST should validate");
        assert_eq!(ast.goal, "ship release");
        assert_eq!(ast.tasks.len(), 2);
    }

    #[test]
    fn rejects_unsupported_ast_version() {
        let ast_text = r#"{
          "ast_version":"9.9",
          "goal":"x",
          "tasks":[]
        }"#;
        let ast = parse_ast(ast_text).expect("json should parse");
        let err = validate_ast(&ast).expect_err("version mismatch should fail");
        assert!(err.contains("unsupported ast_version"));
    }

    #[test]
    fn emits_trace_skeleton_with_contract_version() {
        let ast_text = r#"{
          "ast_version":"1.1",
          "goal":"hello",
          "tasks":[{"name":"a","after":[]},{"name":"b","after":["a"]}]
        }"#;
        let ast = parse_ast(ast_text).expect("json should parse");
        validate_ast(&ast).expect("ast should validate");
        let trace = build_trace_skeleton(&ast);
        assert_eq!(trace.trace_version, TRACE_VERSION);
        assert_eq!(trace.goal, "hello");
        assert_eq!(trace.execution.mode, "sequential");
        assert_eq!(trace.execution.max_parallel, 1);
        assert_eq!(
            trace.execution.levels,
            vec![vec!["a".to_string()], vec!["b".to_string()]]
        );
        assert_eq!(trace.task_order, vec!["a".to_string(), "b".to_string()]);
    }

    #[test]
    fn rejects_cycle_in_plan() {
        let ast_text = r#"{
          "ast_version":"1.1",
          "goal":"cycle",
          "tasks":[
            {"name":"a","after":["b"]},
            {"name":"b","after":["a"]}
          ]
        }"#;
        let ast = parse_ast(ast_text).expect("json should parse");
        let err = validate_ast(&ast).expect_err("cyclic plan should fail");
        assert!(err.contains("cycle detected in plan"));
    }

    #[test]
    fn emits_parallel_levels_for_fanout_plan() {
        let ast_text = r#"{
          "ast_version":"1.1",
          "goal":"fanout",
          "tasks":[
            {"name":"lint","after":[]},
            {"name":"test_suite","after":[]},
            {"name":"deploy_prod","after":["lint","test_suite"]}
          ]
        }"#;
        let ast = parse_ast(ast_text).expect("json should parse");
        validate_ast(&ast).expect("ast should validate");
        let trace = build_trace_skeleton(&ast);
        assert_eq!(trace.execution.mode, "parallel");
        assert_eq!(trace.execution.max_parallel, 2);
        assert_eq!(
            trace.execution.levels,
            vec![
                vec!["lint".to_string(), "test_suite".to_string()],
                vec!["deploy_prod".to_string()]
            ]
        );
        assert_eq!(
            trace.task_order,
            vec![
                "lint".to_string(),
                "test_suite".to_string(),
                "deploy_prod".to_string()
            ]
        );
    }
}
