# T1 protocol: bounded tool-assisted generation

**Default track for new runs.** T0 and agent-pilot require explicit selection.
Without verified external T1 controls, stop and ask; never silently downgrade.

Version: **astrovis-t1-20261123**, for new runs. Provider-quota waits may now
pause the stage clock; numerical budgets are unchanged. Historical and already
pinned runs retain their recorded policies; this revision does not reopen,
certify or rescore them. The [previous contract](../submission/protocols/astrovis-t1-20261110/t1_protocol.json)
is retained for older submissions.
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
| Stage wall time, excluding documented provider-quota waits | 2,400 seconds |
| Active checks / final submissions | One at a time / one |

Charge an admitted request/check **before dispatch**, including errors and
timeouts. Reject over-budget actions without launching them. No budget refunds,
extra sessions or operator-side candidate runs. Persist counters and the remaining
stage time; interruptions count except for the documented quota waits below.
Unknown usage must stay unknown, never be reported as zero or controlled T1.
Perform environment smoke tests on synthetic inputs before benchmark sessions.

A model request is one provider inference invocation, not one code revision or
one tool call. Finish recording the last admitted response and any already
requested tools that remain permitted by the other limits; then freeze before
a further model request. Do not discard the last allowed response or grant an
extra model turn just to submit it. Check 3 always closes the check/revision loop.

## Provider quota exhaustion and resumption

An unfinished stage may enter `paused_provider_quota` when a documented provider
quota/usage-limit error prevents inference. This is not a missing submission or
a terminal stage. After the provider allowance resets, resume the **same**
UID/stage, conversation, candidates and harness/model configuration.

- Keep all charged requests, known tokens, check counts and candidate hashes.
  A failed admitted request still counts; an account quota reset does **not**
  reset benchmark budgets. Unknown usage blocks resumption pending reconciliation.
- Pause only after all in-flight requests/checks have settled and usage is known,
  while the stage still has budget. No solver calls, candidate execution,
  edits or human hints during the pause. Do not poll with inference requests.
- Exclude only this recorded wait from the 2,400-second stage clock. On resume,
  retain the unused time; never grant a fresh 40 minutes. All other interruptions
  and active work still count. Each check retains its 600-second cap.
- Record quota error evidence, UTC pause/resume times, cumulative wall-time
  offsets, counters and state hashes in `generation_events.jsonl`. The ledger
  records `elapsed_seconds` (charged time), `wall_elapsed_seconds`, and
  `quota_pauses` (empty when none). Each interval records `start_elapsed_seconds`,
  `end_elapsed_seconds`, `provider_error`, `evidence_ref`, and `usage_known: true`.
  Offsets measure wall time since stage start; waits must not overlap.
- A terminal stage stays closed, including a scientific failure or an exhausted
  benchmark budget. Do not restart it, replace its answer or switch providers.

Use this policy only with a supervisor that persists and enforces quota pauses.
Existing pinned runs need a separately recorded, explicitly approved migration;
do not silently change their contract or erase earlier terminals.

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
