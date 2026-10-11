# Console (Angular 19)

Operator console for the Services AI Platform: sign in with an API token + tenant,
then browse runs and traces, triage the approval inbox, manage agents, ask grounded
questions in the playground, and view usage.

- Dev: `npx ng serve` (expects the API on `http://localhost:8000` or set `apiUrl` in `src/environments/environment.ts`).
- Test: `npx ng test --watch=false --browsers=ChromeHeadless` (needs Chrome).
- Production build: `npx ng build --configuration=production` (served via `nginx.conf` in Docker).
