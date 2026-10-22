---
type: scar
status: active
created: 2026-10-22
updated: 2026-10-22
summary: A command named like the plugin's skill takes the skill's slash slot; the Skill tool then says 'already loaded' and the skill text never arrives
paths: [plugins/*/commands/*]
---

# A plugin command with the plugin's own name shadows its skill

## What happened

The command file `ship-execute.md` under the executor plugin's `commands/` directory registered as `/ship-execute:ship-execute`, the same identifier the plugin's skill gets as a slash command. In a headless run of `/ship-execute:ship-execute <plan>` on 2026-10-22, the command's text ran, the agent called the Skill tool as the command says, and the harness answered "Skill /ship-execute:ship-execute is already loaded above; instructions unchanged". The skill text was never in the context; the agent noticed and read `SKILL.md` by hand. The harness's own registry shows the shadowing: `ship-execute:ship-execute` appeared once in `slash_commands` while every other plugin's skill appeared beside its command. The planner's command is `ship-plan`, so it had no such problem.

## Tripwire

If a plugin's `commands/<name>.md` has the same name as the plugin (and so as its skill), rename the command. Check with a headless run: after the Skill call, the transcript must contain "Base directory for this skill"; "already loaded above" means the command took the skill's slot.

## Why it hurt

The executor ran its whole first live test without its skill text. It happened to recover because the agent read the file; a less careful agent would have built the plan from the command's four lines.

## Don't do this

Do not name a command after the plugin. `ship-execute`'s command is now `build` (`/ship-execute:build`); the bare `/ship-execute` reaches the skill itself.
