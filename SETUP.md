## Volumes

* `/config` = Directory where `settings.yml` configuration file will be stored in.
* `/log` = Directory where logs will be generated and stored.
* `/tmp` = Directory where backup activites will be performed in. This size will depend on how much data from databases or files that needs to be backed up. This directory will be cleaned up after every backup activity.

## Environment Variables

| Environment Variable                   | Default | Value Req.                                | Example                |
| :------------------------------------- | ------- | ----------------------------------------- | ---------------------- |
| HAWKUPS_LOG_TYPE                       | file    | both,file,syslog                          | both                   | 
| HAWKUPS_LOG_LEVEL                      | DEBUG   | DEBUG,INFO,WARN,ERROR                     | INFO                   |
| HAWKUPS_LOG_SERVER                     | (null)  | Blank or FQDN/IP Address w/ Optional Port | syslog.example.com:514 |
| HAWKUPS_DESTINATIONS__(name)__PASSWORD | (null)  | Blank or password value                   | P@sswOrd               |
| HAWKUPS_JOBS__(name)__PASSWORD         | (null)  | Blank or password value                   | P@sswOrd               |
| HAWKUPS_ALERTS__(name)__TOKEN          | (null)  | Secret value                              | (token here)           |

Password credentials is recommended to be defined as an environment variable than doing inside `settings.yml` configuration file for security reasons. Here is an example of how to define the environment variable for an alert/destination/job's credential:

### Alert Config Example

Add `token` under `data` section:

```yaml
  - name: example-webhook-alert
    success: false
    failure: true
    webhook:
      url: https://api.pushover.net/1/messages.json
      data:
        user: user_key_here
```

Environment variable: `HAWKUPS_ALERTS__example_webhook_alert__TOKEN`

### Destination Config Example

Add `password` under `sftp` section:

```yaml
destinations:
  - name: example-sftp-server
    sftp:
      server: sftp
      port: 22
      username: example
      path: /upload
    retention: 7d
```

Environment variable: `HAWKUPS_DESTINATIONS__example_sftp_server__PASSWORD`

### Job Config Example

Add `password` under `postgresql` section:

```yaml
jobs:
  - name: example-podb-server
    postgresql:
      server: postgresql
      port: 5432
      username: bckupmgr
      ssl: disable
      excludes: []
    destination: example-sftp-server
    retention: 2d
    alert: example-alert
```

Environment variable: `HAWKUPS_JOBS__example_podb_server__PASSWORD`

## Starting Application
### Docker
```bash
docker run --name backup \
    -v ./path/to/config:/config \
    -v ./path/to/log:/log \
    -v ./path/to/tmp:/tmp \
    -e HAWKUPS_LOG_LEVEL=INFO \
    -p 5000:5000 \
    -p 9100:9100 \
    atomicbeast101/hawk-backup:latest
```

### Docker Compose
```yaml
services:
    backup:
        container_name: backup
        image: atomicbeast101/hawk-backup:latest
        environment:
            HAWKUPS_LOG_LEVEL: INFO
        volumes:
            - ./path/to/config:/config
            - ./path/to/log:/log
            - ./path/to/tmp:/tmp
        ports:
            - 5000:5000
            - 9100:9100
```
