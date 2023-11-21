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
apt-get install -y redis-server redis-tools build-essential make python3 python3-redis

# 2. Copy/move files
mv service/* "$INSTALL_DIR/"
chown -R "root:root" "$INSTALL_DIR"
chgrp "$SERVICENAME" "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/data"
chown -R "$SERVICENAME:$SERVICENAME" "$INSTALL_DIR/data"
chmod 0770 "$INSTALL_DIR/data"
chmod +x "$INSTALL_DIR/start-server.sh"

# 3. Compile
pushd .
cd $INSTALL_DIR
make
popd


# 4. Configure startup for your service
# Typically use systemd for that:
# Install backend as systemd service
# Hint: you can use "service-add-simple '<command>' '<working directory>' '<description>'"
service-add-simple "$INSTALL_DIR/start-server.sh" "$INSTALL_DIR/" "RedisBBQ service"
systemctl disable redis

# Example: Cronjob that removes stored files after a while
# cronjob-add "*/6 * * * * find $INSTALL_DIR/data -mmin +45 -type f -delete"



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
