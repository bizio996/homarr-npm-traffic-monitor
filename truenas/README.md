# TrueNAS SCALE Custom App installation

This folder documents installing the **companion collector**, not a Homarr agent.

1. In TrueNAS **Datasets**, create an application dataset, e.g. `POOL_NAME/apps-custom/npm-collector` (use the actual pool name). Never create the collector manually under the TrueNAS-managed `ix-apps` dataset.
2. Copy `collector/collector.py` and `collector/Dockerfile` to the new dataset root. The Dockerfile must exist at the `build.context` path.
3. Create `/mnt/POOL_NAME/apps-custom/npm-collector/.env` using `collector/.env.example`, providing `NPM_EMAIL`, `NPM_PASSWORD`, and a random `COLLECTOR_KEY` (at least 24 characters). For the TrueNAS YAML, `NPM_URL` is configured under `environment`; **do not also add `NPM_URL` or `NPM_EMAIL` as conflicting overrides**. Avoid sharing passwords or API keys. An `NPM_LOGS_PATH` line in `.env` is unused in this TrueNAS YAML because the host volume is specified in the Compose file.
4. Determine the source of NPM's `/data` mount with `docker inspect <NPM_CONTAINER> --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'`. Confirm the host `logs` directory exists, then replace the `volumes` source in `truenas/compose.yaml`. Use a read-only (`:ro`) mount.
5. Update `build.context`, `env_file`, `NPM_URL`, and optionally port `8787` in `truenas/compose.yaml`. Use a collector URL reachable from Homarr (not the NPM admin interface). Limit access to the collector port to trusted clients.
6. TrueNAS **Apps → Discover Apps → Install via YAML**: give the app a name and paste the contents of `truenas/compose.yaml`. Once deployed, verify `npm-homarr-collector` is running.
7. From TrueNAS, authenticate to the collector using `Authorization: Bearer <COLLECTOR_KEY>` against `http://127.0.0.1:8787/snapshot`. Expect JSON with `hostCount`, `enabledCount`, `totals`, and `hosts`.
8. In Homarr **Custom Widget → Configure sources** set Base URL to `http://<TRUENAS_LAN_IP>:8787`, auth Bearer with the same key, request ID `snapshot`, method GET, path `/snapshot`.

## Troubleshooting

- `failed to read dockerfile`: `collector.py` and `Dockerfile` not copied to the `build.context` path.
- HTTP `401` from collector: wrong `COLLECTOR_KEY` in Homarr; reload the application after updating `.env` (a simple restart may not reload env-file values).
- HTTP `502` from collector: inspect collector logs, NPM API credentials and log permissions. If NPM's API responds `Invalid email or password`, test with a dedicated read-only NPM account.
- `<!DOCTYPE html>` in Homarr `data.snapshot`: Homarr Base URL points at NPM's UI rather than port 8787 of the collector.
- `hostCount: 0` on an otherwise successful response: verify account access to NPM Proxy Hosts.

Do not commit your real `.env`, NPM hostnames/IPs, access logs, screenshots containing private domains, or credentials.
