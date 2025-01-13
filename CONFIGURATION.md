## Configuration

All configuration is done in `settings.yml` file under `/config` directory in Docker container. This application has a built-in YAML schema that will validate the configuration and stop the application if it does not meet the citeria. It will also perform test connections to all destinations to ensure it works before enabling any automated backups.

Example of the configuration can be found [here](settings.yml).

### Reference

```yaml
system:
  prometheus:
    # Required: Boolean
    # NOTE: Enable/Disable Prometheus monitoring to see status of the backup jobs
    enabled: true
    # Required: Port between 1 and 65535
    port: 9100

# Optional: This can be an empty list (example: alerts: [])
alerts:
  # Required: Name that can only be alphanumeric, "-" and "_" symbols
  - name: example-webhook-alert
    # Required: true/false if alert should be sent for any successful backup job
    success: false
    # Required: true/false if alert should be sent for any failed backup job
    failure: true
    # Supported types: webhook, notifiers
    webhook:
      # Required: URL endpoint for webhook call
      url: http://host.docker.internal/webhook
      data:
        # Optional: Value defined to pass over to alert. Can also be defined via environment variable (example: HAWKBACKUP_ALERTS__example_webhook_alert__USER)
        user: user-token-here
        # Optional: Value defined to pass over to alert. Can also be defined via environment variable (example: HAWKBACKUP_ALERTS__example_webhook_alert__TOKEN)
        token: api-token-here

  # Required: Name that can only be alphanumeric, "-" and "_" symbols
  - name: example-pushover-alert
    # Required: true/false if alert should be sent for any successful backup job
    success: false
    # Required: true/false if alert should be sent for any failed backup job
    failure: true
    # Supported types: webhook, notifiers
    notifiers:
      # Required: Type of notification that is supported by notifiers
      type: pushover
      # Required: Attributes to pass along for notifiers' notification type (message attribute will be added automatically via the application)
      data:
        # Optional: Value defined to pass over to alert. Can also be defined via environment variable (example: HAWKBACKUP_ALERTS__example_pushover_alert__USER)
        user: user-token-here
        # Optional: Value defined to pass over to alert. Can also be defined via environment variable (example: HAWKBACKUP_ALERTS__example_pushover_alert__TOKEN)
        token: api-token-here

# Required: Must have at least one destination to send backups to
destinations:
  # Required: Name that can only be alphanumeric, "-" and "_" symbols
  - name: example-sftp-server
    # Supported types: sftp
    sftp:
      # Required: SFTP FQDN or IP Address endpoint
      server: sftp
      # Required: SFTP port between 1 and 65535
      port: 22
      # Required: SFTP username
      username: example
      # Optional: SFTP password defined here or via environment variable (example: HAWKBACKUP_DESTINATIONS__example_sftp_server__PASSWORD)
      password: 1234
      # Required: Path in SFTP endpoint, unsure? Use / instead
      path: /upload
    # Required: Default timeframe of backups to keep up to. Daily is only supported at the moment.
    retention: 7d

# Optional: List of jobs can be empty, but then you wouldn't have any backups to perform...
jobs:
  # Required: Name that can only be alphanumeric, "-" and "_" symbols
  - name: example-podb-server
    # Supported types: postgresql, mysql, mongodb, files
    postgresql:
      # Required: Database server FQDN or IP Address endpoint
      server: postgresql
      # Required: Database server port between 1 and 65535
      port: 5432
      # Required: Database username
      username: bckupmgr
      # Optional: Database password defined here or via environment variable (example: HAWKBACKUP_JOBS__example_podb_server__PASSWORD)
      password: 1234
      # Required: SSL option to use to connect to database server
      # Values supported: disable, allow, prefer, require
      ssl: disable
      # Required: List of database to not include in the backup (can be set empty if none). This is on top of the default ones included: template0, template1, postgres
      excludes: []
    # Required: Name of destination to send backups to. Name must exist under destinations section above.
    destination: example-sftp-server
    # Optional: Timeframe of backups to keep up to. Daily is supported at the moment. This will overwrite the default value in the destination mentioned above.
    retention: 2d
    # Optional: Name of alert to notify user(s) of backup status. Name must exist under alerts section above.
    alert: example-webhook-alert

  # Required: Name that can only be alphanumeric, "-" and "_" symbols
  - name: example-mydb-server
    mysql:
      # Required: Database server FQDN or IP Address endpoint
      server: mysql
      # Required: Database server port between 1 and 65535
      port: 3306
      # Required: Database username
      username: root
      # Optional: Database password defined here or via environment variable (example: HAWKBACKUP_JOBS__example_mydb_server__PASSWORD)
      password: 1234
      # Required: List of database to not include in the backup (can be set empty if none). This is on top of the default ones included: information_schema, mysql, performance_schema, sys
      excludes: []
    # Required: Name of destination to send backups to. Name must exist under destinations section above.
    destination: example-sftp-server
    # Optional: Name of alert to notify user(s) of backup status. Name must exist under alerts section above.
    alert: example-webhook-alert

  # Required: Name that can only be alphanumeric, "-" and "_" symbols
  - name: example-modb-server
    mongodb:
      # Required: Database server FQDN or IP Address endpoint
      server: mongodb
      # Required: Database server port between 1 and 65535
      port: 27017
      # Required: Database username
      username: root
      # Optional: Database password defined here or via environment variable (example: HAWKBACKUP_JOBS__example_modb_server__PASSWORD)
      password: 1234
      # Required: List of database to not include in the backup (can be set empty if none).
      excludes: []
    # Required: Name of destination to send backups to. Name must exist under destinations section above.
    destination: example-sftp-server
    # Optional: Name of alert to notify user(s) of backup status. Name must exist under alerts section above.
    alert: example-webhook-alert
```
