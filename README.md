# HawkBackup

Single platform that performs automated database and file-based backups from various servers and pushes them to an internal/external destination such as SFTP endpoint. This was built to make the whole backup setup as convenient as possible without having to add additional services on every server hosting database or files. All activities from monitoring to starting jobs to configuration are done via API calls. There would be no dependencies needed on targets (database servers, for example) in order to perform these backups.

## Features

* Performs backup from a docker-compose setup, can run on any device that supports Docker (amd64 architecture currently supported. aarch64 is not supported due to no architect options for MongoDB CLI packages).
* Send out notifications on successful and/or failed backups via [Notifiers](https://github.com/liiight/notifiers).
* Supports tracking history of backups and performing data retention activities

## Dependencies

Please see docker-compose.yml file example of how it runs, however it only needs three things:
* Redis cache server for tracking background jobs
* Database to store configuration and backup metrics in
* Temporary storage for storing backup activities (as well as long-term storage if using `local` destination type)

## Limitations

* Cannot run on Synology NAS that has aarch64 architecture CPUs.

## Links

* [Setup](SETUP.md)
* [Configuration](CONFIGURATION.md)
* [Swagger API Doc]() <-- to add later

## Services Supported for Backups

| Services      | Limitations |
| :------------ | ----------- |
| PostgreSQL    | N/A         |
| MySQL/MariaDB | N/A         |
| MongoDB       | N/A         |
| Files         | N/A         |

## Destinations Supported

| Destinations | Limitations |
| :----------- | ----------- |
| SFTP         | N/A         |
| Directory    | N/A         |

## Future Plans

* Perform ansible playbooks to backup odd-end things such as network equipment (switches, routers, etc.)
* Expand destination options outside of SFTP & Directory.
