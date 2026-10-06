# Terraform and other infrastructure code: where to look

What is easy to miss in infrastructure changes, and which fixes look right and are not. A match is a place to look, not a finding: say what happens here first. Behaviour and defaults change between versions and with repository or organisation settings; check the version in use, and say when a claim depends on a setting you cannot see. You are reading code, not a plan: say which resources you expect to be created, changed, replaced or destroyed, and that the plan has to confirm it. The same questions apply to OpenTofu, Pulumi, CloudFormation and CDK with their own mechanisms.

## Changes that destroy

- **A renamed or moved resource is a destroy and a create** unless the code says otherwise: changing a resource's name, moving it into or out of a module, or renaming a module, without a `moved` block (Terraform 1.1 and later) or a state move. For a database, a volume, a bucket or a key that is data loss.
- **`count` and `for_each`.** Removing an element from the middle of a `count` list shifts every later index and replaces those resources; switching between `count` and `for_each` changes every address.
- **Arguments that force replacement.** Some attributes cannot be changed in place (an identifier, an engine, an availability zone, an encryption setting). The provider's documentation for the version in use says which; if you are not sure, say that the plan must be checked for "must be replaced".
- **What protects stateful resources:** `lifecycle { prevent_destroy = true }`, the service's own deletion protection, a final snapshot, backups with a retention period, versioning on buckets. A data store with none of these is one mistaken apply from gone.
- `removed` blocks (1.7 and later) and `terraform state rm` drop a resource from state without destroying it; check that this is what was meant.

## State and plans

- **State holds secrets in the clear** (passwords, generated keys, tokens) whatever is marked `sensitive`, which only hides values from output. A remote backend with encryption, access control and locking is the baseline; local state, or state committed to the repository, is a finding. Newer versions offer ephemeral values and write-only arguments that keep some secrets out of state where the provider supports them.
- **Plan output** shows values too. A pipeline that posts plans to a pull request publishes them to everyone who can read it.
- **Apply what was reviewed.** An apply that re-plans (`terraform apply -auto-approve` with no saved plan file) applies whatever is true at that moment, not what a person looked at. Routine use of `-target` or `-refresh=false` hides drift.
- **A plan is code execution.** Data sources, the `external` data source, provisioners and module downloads run during plan and apply with the pipeline's credentials. Planning an untrusted pull request with real credentials is running an outsider's code with them.

## Exposure and privilege

- Ingress from `0.0.0.0/0` or `::/0` on administrative or data ports; a database or cache marked publicly accessible; a bucket policy or access setting that allows anyone; a load balancer or function URL with no authentication in front of something internal.
- IAM: `Action: "*"` or `Resource: "*"` beyond what the workload needs; `Principal: "*"`; a trust policy that lets any repository, branch or account assume a role; long-lived access keys created in code (they end up in state).
- Provider and cloud defaults differ by version and by account settings. Check the default for the version in use before reporting "missing encryption" or "public by default", or say that you could not.

## Reproducibility

- Provider constraints in `required_providers` and a committed `.terraform.lock.hcl`; modules from a registry without a version or from git without a ref resolve to whatever is newest.
- Environments that share one state or one workspace, or variables whose defaults are production values, make a change meant for one environment land in another.
- `ignore_changes` on an attribute hides drift in it for good; `create_before_destroy` matters for anything that must not disappear during replacement.
- Provisioners (`local-exec`, `remote-exec`) and `null_resource` make an apply depend on the machine it runs on and are not undone on destroy.

Not findings on their own: `~>` version constraints; missing tags; no `prevent_destroy` on stateless resources; a module's internal structure; resources the project's documents say another team's pipeline applies.
