# Expected: fixture-3-looks-risky

Everything here that a best-practice checklist flags is either the project's stated policy or settled by what the user said. The right review finds nothing that blocks, says what it checked, and says what it could not see.

## Must not report as a problem

- **A single replica**, no PodDisruptionBudget, no autoscaler: the user said short outages are acceptable.
- **Base images and actions by version tag:** the stated policy.
- **The build stage running as root.** The final stage is distroless with a numeric non-root user.
- **No `HEALTHCHECK`** in the Dockerfile: Kubernetes probes are defined.
- **No CPU limit.**
- **`COPY . .` in the build stage:** only `/out/admin` is copied into the final image.
- No CHANGELOG, runbook, dashboards, canary or load test.

## Acceptable

One or two remarks at the lowest level, if true and marked optional: for example, there is no `.dockerignore` shown, which only affects build speed here; the rollout strategy is the default, which keeps the old pod until the new one is ready. Noting that `/livez` and `/readyz` handlers were not in the fixture, so what they check could not be confirmed, is good coverage reporting.

## Shape

"I found nothing that blocks this in what I examined", with the reason each risky-looking thing is fine, and a coverage line: what could not be seen (the probe handlers, the cluster, how the image tag is set at deploy time, branch protection) and that nothing was run. It does not call the setup production-ready or approved.

## Fails the fixture

Any must-fix or should-fix finding; three or more optional items; a list of generic hardening advice; no statement of what could not be seen.
