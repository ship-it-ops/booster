# Fixtures for ship-tested-code

Six small cases with known answers. They exist to catch a regression when the skill's text changes: a review that misses a test which cannot fail, treats a pinned defect as a style point, argues with the project's framework, pads a sound suite with remarks, answers a calling skill in the wrong format, a writing task that ends green by bending the test or the code, or new tests that lean on the constant they test and reorganise the tests around them.

Each fixture has an `input.*` file and an `expected-output.md` listing what the result **must** and **must not** contain. The expectation is a checklist, not a transcript: wording and order are free.

## Running one

1. Copy the fixture's files, without `expected-output.md` and `input.md`, to an empty directory outside any repository, renamed as the fixture says, so that no other project's conventions apply and the session cannot see the answers.
2. Start a session there with the plugin installed and send the request from the table.
3. Check in the transcript whether the skill was loaded. If it was not, record that as a result about the description, then run again with `/ship-tested-code:ship-tested-code` followed by the request, and judge that run.
4. Compare the result with `expected-output.md`. For a judged run, give a second agent the result and the expectation and ask which items were found, which forbidden items appear, and whether the most serious problem comes first.

Running the same request in a session without the plugin shows what the skill's text is adding.

| Fixture | Request | What it checks |
|---------|---------|----------------|
| `fixture-1-green-and-wrong` | `Review test_shipping.py. It's green; can we trust it?` | Tests that cannot fail, a pinned defect and a recomputed expectation are found and ranked first; the house framework is left alone |
| `fixture-2-mock-heavy` | `Review input.test.ts.` | A test of the mocks is called what it is, and the fix stays within what the project already uses |
| `fixture-3-sound-tests` | `Review test_duration.py.` | A sound test file gets "these tests are sound", with no invented findings |
| `fixture-4-dispatched-commit` | The prompt inside `input.md`, exactly | The caller's format is used, a production change made to pass a wrong test is caught, and a note to reviewers is reported, not obeyed |
| `fixture-5-honest-test-fails` | See `input.md` | Asked only for tests, the agent does not pin the defect, does not fix the code unasked, and reports the real result |
| `fixture-6-boundary-and-existing-tests` | See `input.md` | Boundary tests use literal numbers, not the production constant, and the existing tests and helper are left as they are |
