## API Documentation

### GET /api/health

Reports the health of the application.

```bash
> curl -X GET http://localhost:5000/api/health
{
  "success": true
}
```

### GET /api/jobs

Status of the backup jobs along with the timestamp of its next run.

```bash
> curl -X GET http://localhost:5000/api/jobs
{
  "jobs": [
    {
      "active": true,
      "status": "not_running",
      "name": "example-modb-server",
      "next_run": "Wed, 08 Jan 2025 00:00:00 GMT"
    },
    {
      "active": true,
      "status": "not_running",
      "name": "example-mydb-server",
      "next_run": "Wed, 08 Jan 2025 00:00:00 GMT"
    },
    {
      "active": true,
      "status": "not_running",
      "name": "example-podb-server",
      "next_run": "Wed, 08 Jan 2025 00:00:00 GMT"
    }
  ],
  "success": true
}
```

### GET /api/jobs/\<job_name>/status

Get status of a job.

```bash
> curl -X POST http://localhost:5000/api/jobs/example-podb-server/start
{
  "active": true,
  "status": "not_running",
  "name": "example-podb-server",
  "next_run": "Wed, 08 Jan 2025 00:00:00 GMT"
}
```

### POST /api/jobs/\<job_name>/start

Manually run a backup job.

```bash
> curl -X POST http://localhost:5000/api/jobs/example-podb-server/start
{
  "success": true
}
```

### GET /api/alerts

List of all alerts configured in `settings.yml` configuration file.

```bash
> curl -X GET http://localhost:5000/api/alerts
{
  "alerts": [
    {
      "failure": true,
      "name": "example-webhook-alert",
      "success": false,
      "webhook_url": "https://api.pushover.net/1/messages.json"
    },
    {
      "failure": true,
      "name": "example-pushover-alert",
      "notifiers_type": "pushover",
      "success": false
    }
  ],
  "success": true
}
```

### POST /api/alerts/\<alert_name>/test

Test an alert to make sure it works as expected. Example alert data will be generated for it.

```bash
> curl -X POST http://localhost:5000/api/alerts/example-alert/test
{
  "success": true
}
```
