# Hard cases

Read the section that matches. Each says what evidence to get, what counts as proof, and what an honest answer looks like when proof is not available. Tool flags and runtime behaviour differ by version: check the version in use before relying on a detail.

## You cannot reproduce it

- Say so first, in your answer and to yourself. Everything after this is a hypothesis until something shows otherwise.
- Collect what exists: the exact error and when it first appeared; what changed around then (a deploy, configuration, data, a dependency, traffic); who is affected and who is not. The difference between the affected and the unaffected is usually the shortest path to the cause.
- A large log is searched, not read: find the first occurrence of the failure and what precedes it, count by message to see what is new, and compare a failing window with a healthy one.
- Find a code path that would produce exactly what was observed, then demonstrate that mechanism locally (see `SKILL.md`). A local demonstration shows that the mechanism exists, not that it is what happened in the incident: say which, and what would confirm it after release.
- When several causes fit, rank them, give the evidence for and against each, and name the single observation that would tell them apart.
- **Diagnostics are a legitimate deliverable.** A targeted log line, a counter or an assertion at the point where the candidates differ, written the way the project logs, with no secrets or personal data in it, is often the right change to make. Say what to look for in its output.
- A fix made on an unconfirmed cause is allowed only when the user asked for a best effort, and is reported as "changed, not confirmed", with what would confirm it. (A stopgap the user asked for is a different thing: see `SKILL.md`.)

## It fails only sometimes

- When the condition is visible in the code, skip the counting and demonstrate the condition directly: set the clock, fix the order, share the state.
- When reading does not show it, find the rate before changing anything: loop the failing thing while a run is cheap, bounded by time, and check that each run really executed (some build tools replay a cached result), or take the rate from CI history. Without a rate you cannot tell a fix from luck. When the rate is too low to measure here (weekly, CI only), say so and treat it as "You cannot reproduce it".
- The usual conditions: order (run the test alone, then in the suite, then with the order reversed or randomised with a fixed seed); state shared between tests or requests (module-level objects, caches, files, a database not reset); time (the hour, the time zone, a date boundary, a month end); concurrency (two workers, a race between a write and a read, an await that is missing); resources (ports, file handles, memory); something external (the network, a service).
- Make it more likely so it can be studied: loop it, shrink a timeout, add a delay at the suspected point, pin the seed, set the clock or the time zone.
- If adding a log line makes it disappear, that is evidence of a timing problem, not a fix.
- "Fixed" for an intermittent failure means the condition was found and controlled, and you saw it fail on demand before and not after. Otherwise say "not seen in N runs, where it failed about one in M before", and that this is weaker; N clean runs mean little unless N is several times M.
- A retry, a longer timeout, a sleep or a skip is not a fix: it hides a failure whose condition is unknown. If the code under test has the defect, users meet it too.

## It works here and fails there

Compare the two environments item by item, and change one at a time (compare the names of settings, and the values only of the ones in question; do not print a whole environment or a credentials file): the runtime and dependency versions (the lock file against what is installed), configuration and environment variables, the time zone and locale, the operating system and file-system case sensitivity, the data, the order and parallelism of the test run, what else is running. CI differs from a laptop most often in clock and time zone, parallelism, a clean checkout (no leftover build output or local files), and resources.

## It is slow, or memory grows

- Get a repeatable measurement (a command and a number) and find where the time or memory goes, with a profiler or timing the project already has, before changing anything. Write profiler output outside the repository.
- Change one thing, measure again with the same command, and report both numbers and how noisy they are.
- Look for work that grows with the data: a query inside a loop, a list rebuilt on every call, a cache with no bound, listeners or timers that are never removed.
- A leak is shown by growth across repeated identical operations that does not level off, not by one large number.
- Do not trade correctness for speed without saying so, and keep the optimisation to what the measurement justifies.

## The cause is outside the code

- A dependency: show it in isolation with the smallest script that uses only the dependency, check the version in the lock file against the changelog or issue tracker if you can reach it, and say which version fixes it. Propose the version change; make it only when the user asks, and say it was not run if you could not install it. Work around it in the user's code only as a labelled workaround with a pointer to the upstream issue. Never edit installed or vendored packages.
- Configuration, environment or data: show the same code behaving differently under the two values. The fix may not be a code change at all; say what has to change and where, and whether the code should reject the bad value instead of misbehaving.
- Infrastructure (a full disk, a network limit, an expired certificate): say what you can see from here and what you cannot, and what the user should check.

## Something is down right now

- Stopping the damage comes first, and it is the user's decision. Offer the most reversible option before new code: roll back the change, turn the flag off, restore the configuration.
- Before a restart, tell the user what it destroys and what to save first (a thread dump, the logs), if saving it does not delay the mitigation.
- Whatever is done is labelled a mitigation, with the cause still open, what the mitigation hides, and what to watch.
- Run nothing against the live system unless the user names it; otherwise give the user the command and what to look for.
- Afterwards the investigation still happens: a mitigation that stays becomes the next incident.

## Finding the change that broke it

When there is a known good version and a quick check that tells good from bad, searching history is the fastest route. `git log -S<text>` and `git blame` answer many "when did this change" questions with no checkout at all. When a checkout is needed, do it away from the user's working tree:

```bash
git worktree add --detach /path/outside/the/repo/bisect-tmp <bad-commit>
git -C /path/outside/the/repo/bisect-tmp bisect start <bad-commit> <good-commit>
# run the check at each step, then:
git -C /path/outside/the/repo/bisect-tmp bisect reset
git worktree remove --force /path/outside/the/repo/bisect-tmp
```

The worktree has tracked files only: no installed dependencies, no build output, none of the user's uncommitted work, and it should get no copy of `.env` or other credential files. If the check cannot run there, say so instead of forcing it. Read what the check runs before automating it: it executes each old commit's code. Afterwards `git worktree list` shows only the main tree. A commit that "introduced" the failure may only have exposed an older defect: read the change before blaming it.

## Reviewing a postmortem

Use the team's own template and review the reasoning, in this order:

1. **Does the stated cause explain the whole timeline,** including when it started and why it stopped? Is anything asserted that the document's own evidence does not support?
2. **Are the defect, the trigger and the contributing conditions told apart?** "A deploy" is a trigger. What was wrong, and why it was not caught before or noticed sooner, are separate questions.
3. **Impact and cleanup:** who was affected, what data is wrong now, and whether it has been repaired.
4. **Would each action have prevented, detected or shortened this incident?** Is it specific, and does someone own it? "Be more careful" and "add more tests" are not actions.

Problems under 1 and 2 are the serious ones; 3 and 4 come next. Wording that blames a person, and formatting, are one grouped remark at the lowest level unless the caller asked about them.
