# Deploys

- Migrations are numbered SQL files in `migrations/`. The deploy job runs any file not yet recorded in `schema_migrations`, in order, before the new version starts.
- Old and new versions of the app run side by side for several minutes during a rollout.
