# T1 protocol: bounded tool-assisted generation

Version: **astrovis-t1-20261110**, for new runs. The numerical budgets are
unchanged. Historical results retain their recorded protocols; this clarification
does not certify or rescore them.
Compare runs with matching protocol, harness and inputs; do not silently pool
new-policy runs with historical T1 results as controlled replications.

## The workflow

```text
GENERATION — separately for every processing/visualization stage:
  draft → optional check 1 → optional revision/check 2
                          → optional revision/check 3 → freeze

ALL 144 stage submissions frozen
  → original final execution → maintainer judging → aggregate
```

**Two retries means two optional feedback-driven revisions during generation.**
It does not mean three final benchmark executions. A check may fail or time out;
it still counts. The agent may stop earlier. Edits/reasoning before a check use
the model-request/token budget, not an additional uncounted execution allowance.

## Roles and isolation

- **Operator:** prepares inputs, launches isolated sessions, freezes submissions,
  runs the unchanged final evaluator and packages evidence. It may not repair
  the solver's code or provide hints.
- **Solver:** handles exactly one `(uid, stage)` in a fresh session. Processing
  and visualization have independent histories and budgets; unused budget is
  not transferable. Visualization receives the original reference-processing
  context, not the model's processing answer.
- **External supervisor:** enforces tools, filesystem/network isolation,
  counters, deadlines and freezing. A prompt alone is not enforcement. Without
  audited external controls, stop and request an explicitly labelled pilot.

Use the [operator prompt](../LITE72_AGENT_PROMPT.md). Supply the separate
[solver rules](../submission/t1_solver_instructions.txt) only to T1 sessions;
preserve the upstream scientific/system prompt and stage content, and record
the additional tool-policy wrapper separately. Never inject these rules into T0.
The solver must not inherit the operator's conversation or full benchmark JSON.

## Allowed tools and feedback

Only `list_inputs`, `read_text`, `write_candidate`, `run_candidate`, `submit`.
Inputs must be reviewed, stage-specific allowlists without hidden solutions or
reference plots. Candidate code runs in an unprivileged sandbox, not a host shell.
Only predeclared scientific-data network services are permitted.

No browsing, arbitrary filesystem access, installs, subagents, model switching,
human hints or image viewing—even the solver's own plots. Do not expose images
through text encodings. Checks return only bounded runtime, exit/timeout and
sanitized exception feedback; no hidden tests, scores, reference products,
scientific stdout dumps or judge feedback. Raw stdout/artifacts may be saved
operator-side, outside the solver's accessible workspace.

## Budgets: per stage, not per workflow or retry

| Resource | Maximum |
|---|---:|
| Admitted model requests, including transport retries/compaction | 20 |
| Total output tokens, including observable reasoning | 32,768 |
| Output tokens per response | 8,192 |
| Candidate checks | 3: initial check plus two revision/check opportunities |
| Time per check | 600 seconds, or less if stage time is almost exhausted |
| Total stage wall time | 2,400 seconds |
| Active checks / final submissions | One at a time / one |

Charge an admitted request/check **before dispatch**, including errors and
timeouts. Reject over-budget actions without launching them. No budget refunds,
extra sessions, operator-side candidate runs or deadline resets on resume.
Persist the original counters/deadline; stage wall time includes interruptions.
Unknown usage must stay unknown, never be reported as zero or controlled T1.
Perform environment smoke tests on synthetic inputs before benchmark sessions.

A model request is one provider inference invocation, not one code revision or
one tool call. Finish recording the last admitted response and any already
requested tools that remain permitted by the other limits; then freeze before
a further model request. Do not discard the last allowed response or grant an
extra model turn just to submit it. Check 3 always closes the check/revision loop.

## Stop and freeze deterministically

Stop on `submit`, after check 3, or when the next action would exceed a budget.
The supervisor freezes the submission without needing one more model request:

1. **At least one check:** choose the exact last checked candidate, even if it
   crashed. No best-of selection and no later unchecked edit.
2. **No checks:** choose the latest complete candidate and mark it untested.
3. **No complete candidate:** record a missing stage. Do not invent a submission.

Example: A was checked, then the agent wrote B and exhausted its request budget
before checking B. **Submit A**, not B. If A failed and a later checked B also
failed, submit B rather than an earlier successful candidate.

Hash the final normalized code and close the stage. Preserve all 144 terminal
records, including missing stages. Failed checks do not authorize fresh attempts.
An infrastructure problem is recorded, not repaired through an uncounted retry.

## Freeze barrier and final evaluation

Only after every stage is terminal: freeze/hash `generated_benchmark.json`, then
run the original `exec_bench.py` with fresh evaluation caches and unchanged tests.
This final execution is separate from the three candidate checks and gives the
solver **no further feedback or revision opportunity**. Resume only unfinished
execution records after verifying frozen identities; never rerun completed
scientific failures to improve scores. Infrastructure faults need operator review.

Contributors submit unjudged results. The maintainer applies the original
visualization rubric with three judge trials; those trials are not agent retries.

## Evidence for new runs

Use the [manifest template](../submission/run_manifest.example.json). For T1,
record `generation.protocol_id`, the SHA256 of the
[machine-readable contract](../submission/t1_protocol.json), and the solver-rules
SHA256. Log the actual stage packet/wrapper, model calls, tool admissions,
candidate identities, feedback, budgets and freeze decisions operator-side.
Keep T1 `generation_events.jsonl` for review.

Each ledger entry also records `last_checked_code_sha256`,
`latest_complete_code_sha256` (null if absent), and `terminal_reason` from the
contract. With checks, the final code hash must equal the last checked hash;
without checks, it must equal the latest complete hash. These declarations
support auditing; they do not themselves prove isolation or true tool use.

The [submission checker](../scripts/package_lite72_submission.py) verifies the
declared contract and candidate-selection consistency, and automatically includes
the versioned contract/solver rules in the result archive. Legacy unversioned T1
packages remain distinguishable and require review; they are not silently
certified against this version. See [how to submit](SUBMIT_RESULTS.md).
