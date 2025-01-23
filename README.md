# HawkBackup

Single platform based Docker container that performs automated database and file-based backups from various servers and pushes them to an external destination such as SFTP endpoint. This was built to make the whole backup setup as convenient as possible without having to add additional services on every server hosting database or files.

## Features

* Performs backup from a single docker container, can run in a backup server (Synology, for example).
* Send out notifications on successful and/or failed backups via [Notifiers](https://github.com/liiight/notifiers).
* Supports tracking history of backups and performing data retention activities

## Links

* [Setup](SETUP.md)
* [Configuration](CONFIGURATION.md)
* [API Documentation](API_DOC.md)

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
