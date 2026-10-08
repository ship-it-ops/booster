# Pipeline conventions

- GitHub's own actions (`actions/*`) are referenced by major version tag. Third-party actions are pinned to a commit SHA.
- Jobs that hold deploy credentials never run code from a pull request.
