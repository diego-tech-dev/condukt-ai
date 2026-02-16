import type { StandardSchemaV1 } from "@standard-schema/spec";

export interface ContractIssue {
  readonly message: string;
  readonly path: string;
}

export interface ContractValidationResult<TOutput> {
  readonly ok: boolean;
  readonly value?: TOutput;
  readonly issues?: readonly ContractIssue[];
}

export async function validateContract<TOutput>(
  contract: StandardSchemaV1<unknown, TOutput>,
  value: unknown,
): Promise<ContractValidationResult<TOutput>> {
  const result = await contract["~standard"].validate(value);
  if ("issues" in result && result.issues && result.issues.length > 0) {
    return {
      ok: false,
      issues: result.issues.map((issue) => ({
        message: issue.message,
        path: formatPath(issue.path),
      })),
    };
  }

  if ("value" in result) {
    return { ok: true, value: result.value };
  }

  return {
    ok: false,
    issues: [{ message: "contract validation failed", path: "<root>" }],
  };
}

function formatPath(
  path: readonly (PropertyKey | { readonly key: PropertyKey })[] | undefined,
): string {
  if (!path || path.length === 0) {
    return "<root>";
  }

  return path
    .map((segment) => {
      if (typeof segment === "object" && segment !== null && "key" in segment) {
        return String(segment.key);
      }
      return String(segment);
    })
    .join(".");
}
