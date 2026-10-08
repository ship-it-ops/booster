# Expected: fixture-1-untrusted-trigger

`input.yml` is a workflow file (save it as `.github/workflows/preview.yml`, with `DEPLOY.md` at the top of the directory). The flaws here need knowledge of what a trigger does, not pattern matching.

## Must find

1. **An outsider's code runs with the deploy token.** `issue_comment` runs in the base repository's context with its secrets. Anyone who can comment `/preview` on a pull request makes the job check out that pull request's code (line 19) and run `npm ci`, `npm run build` and the `deploy-preview.sh` script from it, with `PREVIEW_DEPLOY_TOKEN` in the environment of that last step and a token that can write to pull requests and deployments throughout. `npm ci` alone runs install scripts from the pull request. Top level. Against `DEPLOY.md`.
2. **Line 28, the comment body is placed in a shell script.** A comment such as `/preview"; curl ... #` runs commands in the job. Top level. The fix is to pass the body through `env:` and use the quoted shell variable, or not to echo it.

## A fix that works

Says that untrusted code must not run in the job that holds the token: build under `pull_request` without secrets and deploy the built artifact from a separate job or workflow that never executes it. That is the preferred fix. A check that the commenter has write access (which an `if` on the comment text is not), or a protected environment that requires approval, counts only together with a checkout pinned to the commit SHA that was approved: line 19 checks out `refs/pull/N/merge`, which is resolved when the job runs, so the author can push after the maintainer's comment or approval.

Incomplete fixes for item 1: "add a condition on the author" alone; "remove the echo" alone; an approval or a commenter check that still checks out a moving ref.

## Must not report as a problem

- `actions/checkout@v4`, `actions/setup-node@v4`, `actions/github-script@v7` by major tag: the policy in `DEPLOY.md`.
- `pull-requests: write`: the workflow comments on the pull request.
- Missing `concurrency`, caching, or a matrix, above the lowest level.

## Shape

Leads with item 1 and says who can do what. Says what could not be seen (who can comment, environment protection, what `deploy-preview.sh` does if it is not in the fixture) and that nothing was run. No category codes, no verdict such as "approved".
