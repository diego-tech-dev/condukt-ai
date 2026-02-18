---
title: "Interface: PipelineTrace"
---

[**condukt-ai**](../../readme/)

***

# Interface: PipelineTrace

Defined in: [pipeline/types.ts:124](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L124)

Top-level trace payload emitted by a pipeline run.

## Properties

### execution

> `readonly` **execution**: `object`

Defined in: [pipeline/types.ts:130](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L130)

#### levels

> `readonly` **levels**: readonly readonly `string`[][]

#### mode

> `readonly` **mode**: `"level_parallel"`

***

### finished\_at

> `readonly` **finished\_at**: `string`

Defined in: [pipeline/types.ts:129](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L129)

***

### pipeline

> `readonly` **pipeline**: `string`

Defined in: [pipeline/types.ts:126](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L126)

***

### started\_at

> `readonly` **started\_at**: `string`

Defined in: [pipeline/types.ts:128](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L128)

***

### status

> `readonly` **status**: `"ok"` \| `"failed"`

Defined in: [pipeline/types.ts:127](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L127)

***

### summary

> `readonly` **summary**: `object`

Defined in: [pipeline/types.ts:136](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L136)

#### failed

> `readonly` **failed**: `number`

#### passed

> `readonly` **passed**: `number`

#### skipped

> `readonly` **skipped**: `number`

#### total

> `readonly` **total**: `number`

***

### task\_order

> `readonly` **task\_order**: readonly `string`[]

Defined in: [pipeline/types.ts:134](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L134)

***

### tasks

> `readonly` **tasks**: readonly [`TaskTrace`](tasktrace/)[]

Defined in: [pipeline/types.ts:135](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L135)

***

### trace\_version

> `readonly` **trace\_version**: `string`

Defined in: [pipeline/types.ts:125](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L125)
