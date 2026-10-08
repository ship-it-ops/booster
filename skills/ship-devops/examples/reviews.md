# Two reviews in the default format

These show tone and proportion for a plain "review this" with no other instructions. When a caller asks for another format, use theirs.

## A change with real problems

The request: "Review my branch before I merge. It adds a nightly export job and tidies the deploy workflow." The project's `DEPLOY.md` says production images are tagged with the commit SHA and that deploys wait for the test job.

```diff
@@ .github/workflows/deploy.yml
 18    deploy:
 19 -    needs: [test]
 19 +    if: always()
 20      environment: production
@@ k8s/export-cronjob.yaml (new)
  1  apiVersion: batch/v1
  2  kind: CronJob
  3  metadata: { name: nightly-export, namespace: prod }
  4  spec:
  5    schedule: "0 2 * * *"
  6    jobTemplate:
  7      spec:
  8        template:
  9          spec:
 10            restartPolicy: OnFailure
 11            containers:
 12              - name: export
 13                image: registry.example.com/api:latest
 14                command: ["sh", "-c", "node scripts/export.js || true"]
```

The review:

> One change has to be reverted before this merges: production deploys no longer wait for the tests. Two things in the new job should be fixed with it.
>
> **must-fix**
>
> - `.github/workflows/deploy.yml:19` — `needs: [test]` was replaced by `if: always()`, so the deploy job starts whether the test job passed, failed or was cancelled. Every merge to `main` now deploys untested code to production. Read against the `test` job at line 9 and `DEPLOY.md` ("deploys wait for the test job"). Restore `needs: [test]` and remove `if: always()` (with both, the deploy still runs when the tests fail); if the aim was to deploy when an unrelated job is skipped, say which job and I can suggest a condition on its result.
>
> **should-fix**
>
> - `k8s/export-cronjob.yaml:14` — `|| true` makes the job exit zero when the export fails, so `restartPolicy: OnFailure` never retries and nothing records that last night's export did not happen. Drop `|| true` so that a failed export fails the Job, and set a `backoffLimit`.
> - `k8s/export-cronjob.yaml:13` — the job runs `api:latest`, while `DEPLOY.md` says production runs commit-tagged images. The nightly job will run whatever was pushed last, including a build that was never deployed. Use the same tag the Deployment uses.
>
> **consider**
>
> - `k8s/export-cronjob.yaml:4` — no `concurrencyPolicy`. If an export ever runs longer than a day, two will overlap. `Forbid` is the usual choice.
>
> I could not see branch protection or the `production` environment's rules, so I do not know whether a required check or an approval would still stop a failing deploy. Nothing was run: the workflow and the job were read, not executed.

What to notice: the opening says what has to happen before the merge. The first finding is a gate that stopped gating, found by reading what the job used to depend on. Each finding says what happens and when. Nothing is said about the size of the change, a missing runbook or resource limits on a nightly job. The last paragraph says what could not be seen from the repository.

## A setup with nothing that blocks

The request: "Can you look over the Dockerfile and the Deployment for the thumbnail service before it goes live? It is an internal tool; a minute of downtime during deploys is fine."

The review:

> I found nothing that blocks this in what I examined.
>
> What I checked: the final image stage sets a numeric `USER` and copies only `dist/` from the build stage, so nothing from the build context or the registry token mount reaches the image (`Dockerfile:14-19`); the entry point is in exec form and `src/server.ts:31` handles `SIGTERM` by closing the listener, so shutdown is clean within the default grace period. The Deployment's liveness probe calls `/livez`, which only returns 200 (`src/health.ts:4`), and readiness calls `/readyz`, which checks the queue connection (`src/health.ts:9`). The image is referenced by the commit tag the workflow sets. A memory request and limit are set.
>
> One thing to know, not to fix: there is a single replica, so a node drain takes the service down until the pod is rescheduled. You said short downtime is acceptable, so I have not listed it.
>
> I could not see the cluster's admission policies or what the service account is bound to. Nothing was run.

What to notice: "nothing that blocks" comes with what was checked and what could not be seen, and does not call the setup production-ready. The single replica is mentioned once because the user's own statement settles it. No list of optional hardening was added.
