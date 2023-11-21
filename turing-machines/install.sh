#!/usr/bin/env bash

set -eux

# Install the service on a fresh vulnbox. Target should be /home/<servicename>
# You get:
# - $SERVICENAME
# - $INSTALL_DIR
# - An user account with your name ($SERVICENAME)

# 1. Install dependencies
# EXAMPLE: apt-get install -y nginx
apt-get update
apt-get install -y g++ golang-go git

# 2. Copy/move files
mv service/* "$INSTALL_DIR/"
mkdir "$INSTALL_DIR/data"
chown -R "$SERVICENAME:$SERVICENAME" "$INSTALL_DIR/data"
# make-append-only "$INSTALL_DIR/data"

# 3. Compile
cd "$INSTALL_DIR"
go build


# 4. Configure startup for your service
# Typically use systemd for that:
# Install backend as systemd service
# Hint: you can use "service-add-simple '<command>' '<working directory>' '<description>'"
service-add-simple "$INSTALL_DIR/turing-machines -serve 2080" "$INSTALL_DIR/" "TuringMachines++ website"

# Example: Cronjob that removes stored files after a while
cronjob-add-root "*/6 * * * * find $INSTALL_DIR/data -mmin +45 -type f -delete"



# Example: Initialize Databases (PostgreSQL example)

# Example: 5. Startup database (CI DOCKER ONLY, not on vulnbox)
# if detect-docker; then
#     EXAMPLE for PostgreSQL: pg_ctlcluster 11 main start
# fi

# Example: 6. Configure PostgreSQL
# cp $INSTALL_DIR/*.sql /tmp/
# sudo -u postgres psql -v ON_ERROR_STOP=1 -f "/tmp/init.sql"

# Example: 7 Stop services (CI DOCKER ONLY)
# if detect-docker; then
#     pg_ctlcluster 11 main stop
# fi
