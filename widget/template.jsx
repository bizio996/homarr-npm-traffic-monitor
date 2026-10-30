<Stack gap="sm">
  <Group justify="space-between">
    <Text fw={700} size="md">Nginx Proxy Manager</Text>
    <RefreshButton requestId="snapshot" size="xs" />
  </Group>
  {status.snapshot?.loading
    ? <Text size="sm">Loading...</Text>
    : status.snapshot?.ok === false
    ? <Alert color="red">Collector error: {status.snapshot?.error || "Check source URL and credentials"}</Alert>
    : !data.snapshot
    ? <Text size="sm">No data available</Text>
    : <Stack gap="sm">
        <SimpleGrid cols={2} spacing="xs">
          <Paper withBorder p="sm">
            <Text size="xs" c="dimmed">Enabled proxies</Text>
            <Text fw={700} size="xl" c="green">{data.snapshot.enabledCount ?? 0} / {data.snapshot.hostCount ?? 0}</Text>
          </Paper>
          <Paper withBorder p="sm">
            <Text size="xs" c="dimmed">Requests today</Text>
            <Text fw={700} size="xl">{data.snapshot.totals?.requests ?? 0}</Text>
          </Paper>
          <Paper withBorder p="sm">
            <Text size="xs" c="dimmed">Response body traffic</Text>
            <Text fw={700} size="lg">{Math.round(((data.snapshot.totals?.bytes ?? 0) / 1048576) * 100) / 100} MiB</Text>
          </Paper>
          <Paper withBorder p="sm">
            <Text size="xs" c="dimmed">HTTP 4xx / 5xx</Text>
            <Text fw={700} size="lg" c="orange">{(data.snapshot.totals?.http4xx ?? 0) + (data.snapshot.totals?.http5xx ?? 0)}</Text>
          </Paper>
        </SimpleGrid>
        <Group justify="space-between">
          <Text fw={600} size="sm">Proxy Hosts</Text>
          <Badge size="sm" color="blue">{data.snapshot.hostCount ?? 0} hosts</Badge>
        </Group>
        <Text size="xs" c="dimmed">Metrics for {data.snapshot.date ?? "today"}</Text>
        {!data.snapshot.hosts?.length
          ? <Text size="sm">No proxy hosts found.</Text>
          : data.snapshot.hosts.map((host) =>
              <Paper key={host.id} withBorder p="sm">
                <Stack gap="xs">
                  <Group justify="space-between" gap="xs">
                    <Text size="sm" fw={600}>{host.domains?.join(", ") || "Unknown domain"}</Text>
                    <Badge size="sm" color={host.enabled ? "green" : "gray"}>{host.enabled ? "ENABLED" : "OFF"}</Badge>
                  </Group>
                  <Text size="xs" c="dimmed">Upstream: {host.forward || "N/A"}</Text>
                  <Group gap="xs">
                    <Badge size="xs" color={host.ssl ? "teal" : "gray"}>{host.ssl ? "SSL configured" : "No SSL"}</Badge>
                    <Badge size="xs" color="blue">ID {host.id}</Badge>
                  </Group>
                  <SimpleGrid cols={3} spacing="xs">
                    <Stack gap={0}><Text size="xs" c="dimmed">Requests</Text><Text size="sm" fw={600}>{host.requests ?? 0}</Text></Stack>
                    <Stack gap={0}><Text size="xs" c="dimmed">Traffic</Text><Text size="sm" fw={600}>{Math.round(((host.bytes ?? 0) / 1048576) * 100) / 100} MiB</Text></Stack>
                    <Stack gap={0}><Text size="xs" c="dimmed">Errors</Text><Text size="sm" fw={600} c="orange">{(host.http4xx ?? 0) + (host.http5xx ?? 0)}</Text></Stack>
                  </SimpleGrid>
                </Stack>
              </Paper>
            )}
      </Stack>}
</Stack>
