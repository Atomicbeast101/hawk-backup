## Volumes

* `/data` = Directory where the SQLite database will be stored in. Needs to be mounted to keep the config settings for the app.
* `/log` = OPTIONAL: Directory where logs will be generated and stored.
* `/tmp` = Directory where backup activites will be performed in. This size will depend on how much data from databases or files that needs to be backed up. This directory will be cleaned up after every backup activity.
* `/backups` = OPTIONAL: Directory where all backups will be stored if a job has a `directory` based destination.

## Exposed Ports

* `5000/tcp` = API endpoint for the application to view status of jobs or to manually start them.
* `9100/tcp` = Promtheus exporter.

## Environment Variables

### Base Environment Variables

| Environment Variable                   | Default | Value Req.                                | Example                 |
| :------------------------------------- | ------- | ----------------------------------------- | ----------------------- |
| LOG_LEVEL                              | DEBUG   | DEBUG,INFO,WARN,ERROR                     | INFO                    |
| LOG_TYPES                              | (null)  | file,syslog                               | file                    | 
| LOG_SYSLOG_HOST                        | (null)  | Blank or FQDN/IP Address w/ Optional Port | syslog.example.com:514  |
| DATABASE_URL                           | (see below) | URL of the database (based on SQLalchemy) | (see example)       | 
| APP_SECRET_KEY                         | (generated) | Secret key for sessions               | this_is_a_random_secret |
| API_TOKEN                              | N/A     | Token to use for API calls                | this_is_a_random_token  |
| PROMETHEUS                             | FALSE   | True/False to enable prometheus metrics   | TRUE                    |
| API_DOCS                               | FALSE   | True/False to show API docs page          | TRUE                    |

> Default value for DATABASE_URL: sqlite:////data/hawk-backup.db

### Config-Based Environment Variables

For any config you add for alert/destination/job, it's best practice to have a separate environment variable defined before creating them to avoid credentials being stored in the database.

#### Alert Config Example w/ Environment Variable for API Token/Password/Etc

To add a `token` under `data` for `example_alert` webhook alert config, use this environment variable: `HAWK_BACKUP_ALERT__example_alert__TOKEN`

#### Destination Config Example w/ Environment Variable for Password

To add a `password` for `example_destination` destination config, use this environment variable: `HAWK_BACKUP_DESTINATION__example_destination__PASSWORD`

#### Job Config Example w/ Environment Variable for Password

To add a `password` for `example_job` job config, use this environment variable: `HAWK_BACKUP_JOB__example_job__PASSWORD`

## Starting Application

> Highly recommend using docker compose approach as all of my testing & personal use has been in Docker containers and there are three services (redis, app and celery worker) that are needed for this to work.

### Docker Compose
```yaml
services:
  redis:
    container_name: redis
    image: redis:latest
  app:
    container_name: app
    image: atomicbeast101/hawk-backup:latest
    environment:
        LOG_LEVEL: INFO
    ports:
        - 5000:5000
        - 9100:9100
    depends_on:
      - redis
  worker:
    container_name: worker
    image: atomicbeast101/hawk-backup:latest
    command: celery -A app worker --loglevel=INFO
    environment:
      LOG_LEVEL: INFO
    volumes:
      - ./path/to/log:/log
      - ./path/to/tmp:/tmp
      - ./path/to/backups:/backups
    depends_on:
      - redis
```
