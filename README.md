# HawkBackup

Single platform that performs automated database and file-based backups from various servers and pushes them to an internal/external destination such as SFTP endpoint. This was built to make the whole backup setup as convenient as possible without having to add additional services on every server hosting database or files. All configuration is done via a simple YAML config file and no dependencies are needed on clients to perform these backups.

## Features

* Performs backup from a single docker container, can run on any device that supports Docker (if its amd64 or arm64 architecture, aarch64 is not supported due to MongoDB not supporting it)
* Send out notifications on successful and/or failed backups via [Notifiers](https://github.com/liiight/notifiers).
* Supports tracking history of backups and performing data retention activities

## Limitations

* Cannot run on Synology NAS that has aarch64 architecture CPUs.

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
