# How changes reach production

- Every pull request runs CI (`.github/workflows/ci.yml`). Merging to `main` runs the deploy workflow (`.github/workflows/deploy.yml`), which builds the image, runs migrations and rolls out to the `prod` namespace.
- **Actions:** GitHub's own actions (`actions/*`) are referenced by major version tag. Every third-party action is pinned to a full commit SHA.
- **Workflow permissions** are declared per workflow and kept to what the jobs need.
- **Migrations** must work with both the release being deployed and the one before it, because old and new pods run side by side during a rollout. One numbered SQL file per migration in `migrations/`; they run before the new pods start.
- **Images** are built once per commit and tagged with the commit SHA. Production never runs a mutable tag.
- **Secrets** come from the cluster's secret store or GitHub environment secrets. Nothing secret is baked into an image.
- **Probes:** liveness checks only the process; readiness checks the dependencies.
- Terraform in `terraform/` is applied by the platform team from their own pipeline, with remote state. This repository's CI does not apply it.
