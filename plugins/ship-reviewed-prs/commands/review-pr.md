---
description: Review a GitHub pull request and post one review with inline comments (asks before posting locally; posts unattended with --non-interactive).
argument-hint: "[pr-number-or-url] [--non-interactive] [--auto-approve] [--comment-only]"
allowed-tools: Skill, Agent, Read, Write, Edit, Grep, Glob, AskUserQuestion, Bash(python3 *ship-reviewed-prs/scripts/review_pr.py*), Bash(gh pr view *), Bash(gh pr diff *), Bash(gh issue view *), Bash(git show *), Bash(git diff *), Bash(git log *), Bash(git grep *), Bash(git status *)
---

Review the pull request named in the arguments with the `ship-reviewed-prs` skill.

Arguments: $ARGUMENTS

Load the `ship-reviewed-prs` skill with the Skill tool before doing anything else, and follow it; it owns the whole procedure. The first argument, if there is one, is the pull request number or URL; with none, the skill uses the current branch's pull request. Pass every flag (`--non-interactive`, `--comment-only`, `--auto-approve`) on to the skill's `context` command exactly as given: `--non-interactive` is what makes an unattended run post its review.
