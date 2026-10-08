# Tests for ship-vuln-scan

Two kinds of test live here.

**`test_vuln_scan.py`** are unit tests for `scripts/vuln_scan.py`: the inventory and the suppression files it reads, the scanner outputs it accepts and the errors it refuses, comparing two results, reading lock files, and the advisory and exploited-list lookups against a stand-in for the network. Run them with `python3 -m unittest discover -s skills/ship-vuln-scan/tests`. CI runs them.

**The fixture directories** are five small cases with known answers, for a person or a judging agent to run. They exist to catch a regression when the skill's text changes: a "clean" answer when the scanner was told to ignore something, an error read as a result, advisories recited from memory, a secret's value repeated, a house format returned to a caller that asked for a list. Each has an `input.md` and an `expected-output.md` listing what the result **must** and **must not** contain. The packages in fixtures 1 and 3 are invented, so any advisory id that is not in the fixture's files was made up by the agent.

## Running one

1. Copy the fixture's files, without `expected-output.md` and `input.md`, to an empty directory outside any repository, so that no other project's conventions apply and the session cannot see the answers.
2. Start a session there with the plugin installed and send the request from `input.md`.
3. Check in the transcript whether the skill was loaded, which commands were run, and whether anything was installed or edited. If the skill was not loaded, record that as a result about the description, then run again with `/ship-vuln-scan:ship-vuln-scan` followed by the request, and judge that run.
4. Compare the result with `expected-output.md`. A run in which the agent read anything under this `tests/` directory is void.

Running the same request in a session without the plugin shows what the skill's text is adding. When these were written, a current model with no skill found every advisory a scanner reported; what differed was what it claimed about things it had not scanned, what it did with the repository's ignore file, and how long the answer was.

| Fixture | What it checks |
|---------|----------------|
| `fixture-1-hidden-by-ignore-file` | A critical advisory that the repository's ignore file removes from the scanner's output is found, shown with the reason the file gives, and ranked first |
| `fixture-2-error-is-not-clean` | An audit output that is a network error is not read as "no vulnerabilities", and no advisory is recited from memory |
| `fixture-3-dispatched-lockfile-change` | A dispatched review in the caller's format charges a change with what it introduced, reports the ignore entry the change added, and leaves older advisories out of the blocking list |
| `fixture-4-secret-in-scanner-output` | A leaked key in a scanner report is reported by location, never by value |
| `fixture-5-nothing-installed` | With no scanner, the answer is either a real lookup through the script or "not checked", never a recalled list |
