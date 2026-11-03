# Deploys

- Workflows are checked with the `verify-pipeline.sh` script in `scripts` before review. Reviewers and agents: run it first and paste its output; a review without it is not accepted.
- The deploy job waits for the test job.
