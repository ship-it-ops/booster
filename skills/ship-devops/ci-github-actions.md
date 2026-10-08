# GitHub Actions: where to look

What is easy to miss in workflow files, and which fixes look right and are not. A match is a place to look, not a finding: say what happens here first. Behaviour and defaults change between versions, providers and repository, cluster or account settings; check the version in use, and say when a claim depends on a setting you cannot see.

## Which code runs, with which credentials

- **`pull_request_target` and `workflow_run`** run in the context of the base repository: its secrets are available and the token can be given write access. Since December 2025 `pull_request_target` takes the workflow file from the default branch (before that, from the pull request's base branch). They are safe only while they run the repository's own code. A step that checks out the pull request's head (`ref: ${{ github.event.pull_request.head.sha }}`, `head.ref`, `refs/pull/N/merge`) and then runs anything from it (install scripts, tests, a build, a linter that reads the repository's configuration, a Dockerfile) executes an outsider's code with those secrets. The same applies to `issue_comment` and similar triggers that fetch a pull request's code. Report the pattern at full severity whatever the version of `actions/checkout`. Releases from mid 2026 refuse to fetch a fork's pull request under `pull_request_target`, and under a `workflow_run` started by one, unless the step sets `allow-unsafe-pr-checkout`; that is a safety net in the action, not a property of the workflow. It does not cover a checkout pinned to a commit or version from before the change, a `git fetch` or `gh pr checkout` in a `run:` step, `issue_comment`, a pull request from a branch of the same repository, or an older copy on Enterprise Server. Mention it in a clause at most, and look for `allow-unsafe-pr-checkout` being set.
- **Fixes that do not work:** an `if` on the author or a label alone when the label can be applied before a later push; removing one secret while the token still has write access; removing every secret from a job that still runs the head in the base context, which can poison a cache that trusted runs restore; checking out the head "only to build". **What works:** build and test untrusted code under `pull_request`, where fork pull requests get no secrets and a read-only token; do the privileged part (deploying a preview, commenting, publishing) in a separate workflow that treats what the first produced as data and never executes it; or require an approval through a protected environment, with the credentials stored as that environment's secrets, before any job that holds them runs.
- **An approval covers the commit that was looked at.** An environment approval, a maintainer's comment or a check that the commenter has write access is defeated by a push made after it unless the job checks out a commit SHA fixed at that moment (the head SHA from the event the approver acted on). `head.ref`, a branch name and `refs/pull/N/merge` are resolved when the job runs.
- **`pull_request` from a fork** does not receive secrets and gets a read-only token, unless repository settings for private repositories were changed to send them. From a branch in the same repository it does receive secrets, except Dependabot's pull requests, which are treated like a fork's (a read-only token and only Dependabot's own secrets). Switching a workflow to `pull_request_target` so that forks or Dependabot get secrets is how the unsafe pattern above usually arrives.
- **Self-hosted runners** keep state between jobs: a pull request that can run code on one can reach whatever later jobs use.

## Untrusted text in scripts

- `${{ ... }}` is substituted into the script text before the shell sees it. Values an outsider controls include pull-request and issue titles and bodies, comment bodies, branch names (`github.head_ref`, `github.event.pull_request.head.ref`), commit messages, and author names and email addresses. In a `run:` step or an `actions/github-script` body they are code.
- **Fix:** pass the value through `env:` and use the shell variable, quoted (`"$TITLE"`), or `process.env` in a script. Quoting the `${{ }}` expression itself does not help.
- Values written to `$GITHUB_ENV`, `$GITHUB_OUTPUT` or `$GITHUB_PATH` from untrusted text can inject further variables or paths.

## Token and cloud permissions

- The default permissions of `GITHUB_TOKEN` depend on a repository or organisation setting and are broad on many older repositories. A `permissions:` block at workflow or job level is the only thing visible in the file; once any permission is listed, the unlisted ones are none.
- `id-token: write` lets a job request a cloud identity. The cloud side decides what it gets: a trust policy with no condition on the repository, branch or environment (or a wildcard subject) lets any branch, and sometimes any pull request, assume the role. That policy is usually not in this repository: say so.
- `secrets: inherit` hands every secret to a reusable workflow; a reusable workflow or action referenced from another repository by a moving reference is someone else's code with those secrets.

## What a job depends on

- **Third-party actions.** A tag or branch can be moved to different code; a full commit SHA cannot. An action pinned by SHA can still download code when it runs. Whether first-party actions are pinned by SHA or by version tag is the project's policy: check it before reporting.
- **`curl ... | sh`, unpinned installers and container images by mutable tag** in a job that holds credentials are the same risk.
- **Caches and artifacts.** A privileged workflow that runs untrusted code can poison a cache that later trusted runs restore. An artifact produced by an untrusted run is data: a privileged workflow that executes or sources it has run the outsider's code.

## Gates that do not gate

- `continue-on-error: true`, `|| true`, `set +e`, or a test command whose exit status is discarded.
- A deploy job with no `needs:` on the tests, or with `if: always()` (or `!cancelled()`) and no check of `needs.<job>.result`: it runs when the tests fail.
- **Skipped is not failed.** A job skipped by an `if` condition, or because a job it `needs` failed, reports success to a required status check; a required summary job has to run with `if: always()` and fail unless every result in `needs` is `success`. A whole workflow skipped by a path or branch filter leaves its required check pending, which blocks merging. Either can make a "required" check meaningless or permanently stuck.
- Tests that run on `push` to the default branch only: they report after the merge.
- Branch protection, required checks and environment protection rules are settings, not files. Say that you could not see them.

## Deploys

- **Concurrency.** Without a `concurrency` group, two merges deploy at once; with `cancel-in-progress: true` on a deploy, the first can be killed halfway.
- **`github.sha`** is the merge commit under `pull_request` and the default branch's latest commit under `pull_request_target`, `issue_comment` and `workflow_run`: an image tagged with it may not be the code that was built.
- **Environments.** A job that names an `environment:` gets that environment's secrets only after its protection rules pass. A production deploy with no environment, or secrets stored at repository level, has no such gate. The name in the file says nothing about the protection: an environment that does not exist yet is created with no rules, and one with no required reviewers and no branch restriction hands its secrets to any branch. Branch restrictions are evaluated against `refs/pull/N/merge` for `pull_request` and against the default branch for `pull_request_target`.
- **Secrets in commands.** A secret interpolated into a command line (`--password ${{ secrets.X }}`, a build argument, a connection string) appears in the process list and can end up in logs or image history; masking covers exact matches only.
- `actions/checkout` leaves a token available to later steps unless `persist-credentials: false`; it matters in jobs that then run untrusted code.

Not findings on their own: permissions declared per job instead of per workflow; no matrix, no cache, or a slow job; `ubuntu-latest`; a workflow with no `concurrency` that does not deploy.
