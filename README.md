# Nginx Proxy Manager — Hosts & HTTP Traffic Monitor for Homarr 2.x

A **read-only** Homarr 2.x custom widget for [Nginx Proxy Manager](https://nginxproxymanager.com/). Shows enabled proxy hosts, upstream address and port, SSL configuration, daily HTTP request counts, response-body traffic and 4xx/5xx errors. Uses a separate lightweight Python collector to read the NPM API and its access logs.

## Requirements

- Homarr 2.x with Custom Widgets / Workshop support
- Nginx Proxy Manager API (tested by the project author with NPM 2.16.0)
- Docker/Compose host with **read-only** access to NPM's `data/logs` directory
- NPM account with permission to list proxy hosts; use a dedicated account

## Install

1. Download or clone this repository.
2. `cd collector && cp .env.example .env` and edit **all** placeholder values.
3. Generate a random key: `openssl rand -hex 32` and set `COLLECTOR_KEY` in `.env`.
4. Set `NPM_LOGS_PATH` to the host path containing `proxy-host-<id>_access.log`. For TrueNAS SCALE Apps, obtain the exact mount source with `docker inspect <npm-container>`; never assume it lives under your visible datasets.
5. Start: `docker compose up -d --build`. On TrueNAS SCALE, use the dedicated **[`truenas/compose.yaml`](truenas/compose.yaml)** and **[TrueNAS installation guide](truenas/README.md)** through **Apps → Install via YAML**, with valid dataset paths and read-only NPM log access.
6. Import `widget/widget.json` in **Homarr → Management → Custom Widgets**.
7. Configure source `default`: **Base URL** = the collector URL reachable from **Homarr server**, for example `http://collector-host.example.internal:8787`; **auth** = Bearer token with the value of `COLLECTOR_KEY`. Request `snapshot` remains `GET /snapshot`.
8. In the widget workbench click **Try and preview**, confirm `data.snapshot.hostCount` is nonzero, **Save**, add the widget to a board and save the board.

**Important:** Do **not** point the widget at the NPM admin interface (port 81 or other UI proxy URL). It must point at the **collector**. A request that returns an HTML document rather than JSON means the source URL is wrong.

## Verify

Request `GET /snapshot` with `Authorization: Bearer <COLLECTOR_KEY>`; success is JSON with `date`, `hostCount`, `enabledCount`, `totals`, `hosts`. A `401` means the collector key is wrong; `502` means the collector couldn't query NPM. Check `docker logs` without disclosing secrets.

## Metrics and limitations

- `enabledCount` means *enabled in NPM*, **not** a live uptime/health check.
- `ssl` indicates a configured certificate ID, **not** validated expiry or certificate health.
- `bytes` is the sum of NPM access log response-body byte counts, not full bidirectional network throughput; widget presents MiB (1 MiB = 1,048,576 bytes).
- `requests`/status codes are counted for the current local date. The collector reads currently active `proxy-host-*_access.log` files; rotated `.gz` logs are not included. For long-term retention or high traffic, prefer Loki/Prometheus/Grafana.
- Access to `NPM_LOGS_PATH` depends on the collector user's file permissions. Do not weaken NPM log permissions indiscriminately.
- Collector results are cached for 60 seconds by default.

## Security / publication

- Never commit `.env`, passwords, API tokens, NPM exports, real hostnames, IPs or unredacted screenshots.
- Use a dedicated least-privilege NPM user and a random collector Bearer token.
- The sample Compose publishes 8787 on the host: **restrict access to your trusted network**. Do not expose it directly to the Internet.
- Homarr source credentials are configured privately per installation and are omitted from Workshop exports; double-check the exported source URL before publishing.
- If you pasted a real password/token into a chat or repository, **rotate it**.

## Screenshot

Add the English, privacy-redacted screenshot to `assets/screenshot-en.png` before publishing. See [screenshot instructions](assets/README.md). Do not use the original screenshot containing private network details.

## Publish

1. Publish this repository to your GitHub account (without `.env`).
2. In Homarr, open **Management → Custom Widgets → Actions → Publish** on your *saved and tested* widget. Workshop publication happens through Homarr; a pull request to the Homarr GitHub repository is not required.
3. Link this GitHub repo in the Workshop description, explain collector dependency, and attach a screenshot with all private hostnames/IPs hidden.

Docs: https://homarr.dev/docs/workshop/ and https://homarr.dev/docs/management/custom-widgets/.

## License

MIT — see [LICENSE](LICENSE).
