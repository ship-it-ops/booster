# Kubernetes manifests: where to look

What is easy to miss in workloads and their rollout, and which fixes look right and are not. A match is a place to look, not a finding: say what happens here first. Behaviour and defaults change between versions, providers and repository, cluster or account settings; check the version in use, and say when a claim depends on a setting you cannot see. What the cluster adds (admission policies, defaults, a service mesh, autoscalers) is not in the manifests: say that you could not see it. For Helm or Kustomize, reason about the rendered result for the environment in question.

## Probes

- **Liveness** failing restarts the container. If the endpoint checks a database or another service, a blip there restarts every pod, drops in-flight work, and fixes nothing. It should fail only when a restart would help.
- **Readiness** failing removes the pod from the Service. With no readiness probe, the pod receives traffic the moment the container starts and the rollout treats a broken pod as available. A readiness probe that checks a shared dependency removes every pod together when it fails: the service returns nothing where it might have returned errors or partial results.
- **Start-up.** A slow start is handled by a start-up probe, not by a long `initialDelaySeconds` on liveness. Check `periodSeconds` times `failureThreshold` against how long the application really takes.
- Open the handler the probe calls before judging it.

## Rollouts

- `strategy: Recreate` stops every pod before starting new ones: downtime on every deploy. It is right only when two versions must never run together.
- With `RollingUpdate`, the defaults (25% surge, 25% unavailable) keep a single replica up, because the unavailable count rounds down to zero; `maxUnavailable: 1` with one replica is an outage.
- A rollout waits for readiness. Without a readiness probe it proceeds through pods that are not working; with `minReadySeconds` unset, a pod that crashes just after becoming ready still counts.
- **Mutable image tags.** With `:latest` the pull policy defaults to `Always`, otherwise to `IfNotPresent`: a re-pushed tag means different nodes run different code. If the tag does not change between releases the manifest is unchanged and applying it starts no rollout. There is nothing to roll back to.
- **Applying is not rolling out.** Applying a manifest succeeds as soon as the API accepts it. Unless the pipeline waits (`kubectl rollout status`, `helm upgrade --wait` or `--atomic`, the GitOps tool's health check), the deploy is green over a rollout that never became ready. Kubernetes marks a stalled rollout as failed at `progressDeadlineSeconds` and does not roll it back.
- A ConfigMap or Secret consumed as environment variables does not reach running pods when it changes; something has to restart them.

## Termination and disruption

- On deletion the container gets `SIGTERM`, then `SIGKILL` after `terminationGracePeriodSeconds` (30 by default). Removal from the Service happens in parallel, not first, so requests still arrive for a moment after the signal: the application has to keep serving briefly, or a `preStop` delay has to cover it. Work longer than the grace period is cut off.
- Without a PodDisruptionBudget, a node drain can evict every replica at once. A budget that allows no disruption on a single-replica workload blocks drains instead.
- Replicas on one node or one zone go together; whether that matters depends on what the user said about availability.

## Resources

- No memory request lets the scheduler place the pod anywhere; no memory limit lets one pod take a node's memory and get its neighbours killed; a limit below what the process really uses is a restart loop.
- CPU limits throttle and many teams set requests only. A missing CPU limit is not a finding by itself.
- A HorizontalPodAutoscaler needs requests to compute utilisation, and fights with a `replicas:` value in a manifest that is re-applied on every deploy.

## Identity and isolation

- `securityContext`: `runAsNonRoot` (needs a numeric user in the image, or `runAsUser` in the pod), `allowPrivilegeEscalation: false`, dropped capabilities, a read-only root filesystem where the application allows it. `privileged`, `hostNetwork`, `hostPID` and `hostPath` mounts give the pod the node.
- The service account's permissions are whatever its role bindings say. A binding to `cluster-admin`, or wildcard verbs and resources, for an application or a CI identity is the usual excess. A mounted service-account token is unnecessary for pods that never call the API.
- Secrets passed as environment variables are visible to everything in the process and in crash dumps; that is a trade-off, not a defect.

## Things that fail quietly

- A Service whose selector does not match the pod labels has no endpoints and no error.
- A manifest with a hard-coded `namespace:` applied with `-n` for a different namespace is rejected; made to work, it deploys into the namespace in the file. Manifests reused for previews or staging often carry the production namespace, secret names and hostnames.
- Migrations in an init container or a start-up command run once per replica, concurrently; many tools take a lock, so the usual cost is every pod waiting behind a long migration and the rollout timing out. Check the tool. Migrations in a Job run once, but a Job applied next to the Deployment is not ordered before the rollout, and the rollout does not stop when it fails, unless the pipeline or a hook makes it wait. Re-applying a Job under the same name with a new image is rejected, because its template cannot be changed.
- CronJobs: `concurrencyPolicy`, a deadline, and what happens when a run fails.

Not findings on their own, beyond the list in `SKILL.md`: one replica for a workload the user has said is internal or tolerant of downtime; no PodDisruptionBudget for a single replica; no autoscaler; no NetworkPolicy in a project that does not use them; secrets as environment variables.
