# timescaledb
* https://docs.timescale.com/self-hosted/latest/install/installation-linux/
* sudo apt install gnupg postgresql-common apt-transport-https lsb-release wget
* sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
* echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" | sudo tee /etc/apt/sources.list.d/timescaledb.list
* wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/timescaledb.gpg
* sudo apt update
* sudo apt install timescaledb-2-postgresql-16 postgresql-client-16
* sudo -su postgres timescaledb-tune

## Add the TimescaleDB extension to your database
* sudo -u postgres psql
* CREATE EXTENSION IF NOT EXISTS timescaledb;