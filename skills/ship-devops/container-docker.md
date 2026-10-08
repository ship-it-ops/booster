# Dockerfiles and images: where to look

What is easy to miss in image builds, and which fixes look right and are not. A match is a place to look, not a finding: say what happens here first. Behaviour and defaults change between versions, providers and repository, cluster or account settings; check the version in use, and say when a claim depends on a setting you cannot see.

## What ends up in the image

- **Build arguments and environment instructions persist.** Every `ENV` is in the image's configuration, and an `ARG` is recorded in the history of the stage that declares it. Declared in the final stage, anyone who can pull the image can read it. Declared only in an earlier stage it is not in the pushed image, but it is in the build cache (including a cache exported to a registry), can be in a provenance attestation, and travels with any file it was written to and that is copied forward. Say which applies.
- **Files persist in the layer that wrote them.** Deleting a file in a later `RUN` does not remove it from the earlier layer. In a multi-stage build, a broad `COPY --from=build /app /app` carries along whatever the build stage wrote there: `.npmrc`, `.env`, `.git`, credentials files, SSH keys.
- **Fix that works:** a build secret mount (`RUN --mount=type=secret,id=...`), or `--mount=type=ssh` for git access, which never writes the value to a layer; and copy only the built output into the final stage. Moving the `ARG` to an earlier stage does not help if the file it wrote is copied forward.
- **No `.dockerignore`** with `COPY . .` sends the whole context, including `.git`, local environment files and build output, into the image.
- A secret that reached a pushed image is compromised: rotate it.

## How the container runs

- **The final stage's user** is its last `USER` instruction or, with none, the base image's: root for most general-purpose bases, already non-root for distroless `:nonroot` and similar. Check the base before saying root; if you cannot see what the base sets, say so. A build stage running as root is normal. Kubernetes' `runAsNonRoot` can only verify a numeric user: an image whose `USER` is a name fails to start under it unless the pod sets `runAsUser`.
- **Process 1 and signals.** The shell form of `CMD` or `ENTRYPOINT` (`CMD node server.js`) puts `/bin/sh -c` in front of the process. Whether the termination signal then reaches it depends on the shell and the line (some shells replace themselves with a single simple command; busybox's and any compound command do not), so the service may be killed at the end of the grace period instead of shutting down cleanly. The exec form (`CMD ["node", "server.js"]`) removes the doubt but is not enough alone: as process 1 the service gets the signal only if it installs a handler for it, or runs under an init. A package-manager script as the entry point (`npm start`) may not forward the signal, depending on the version. A process that does not reap children needs an init (`--init`, `tini`).
- **`HEALTHCHECK`** is used by Docker and Compose. Kubernetes ignores it and uses its own probes.

## What the build depends on

- **Mutable references.** `latest` and every other tag can be re-pushed to different content; a digest cannot. Whether base images are pinned by digest or by version tag is the project's policy; either way something has to update them. `latest` for a production base image, or as the tag production deploys, is worth reporting.
- **Reproducible installs.** `npm install` or `pip install` without a lock file resolves different versions on different days; the lock-file install (`npm ci`, a hashed requirements file) does not. `apt-get update` in a separate layer from `apt-get install` installs from a stale cached index.
- **`ADD` with a URL, and `curl | sh`,** fetch unverified content at build time.
- **One image per environment** (environment-specific build arguments or files) means production runs something that was never tested; build once and configure at run time.

## Compose

- `ports: "5432:5432"` publishes on every interface of the host, not only locally; on a server that is the internet unless something outside the host (a security group, a network firewall) blocks it. A host firewall such as ufw usually does not: Docker's own rules are evaluated first. `127.0.0.1:5432:5432` binds locally.
- `privileged: true`, a mounted Docker socket, or the host's network or process namespace give the container the host.

Not findings on their own, beyond the list in `SKILL.md`: no multi-stage build for a small interpreted service.
