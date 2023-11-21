#!/usr/bin/env bash

set -eux

# Install the service on a fresh vulnbox. Target should be /home/<servicename>
# You get:
# - $SERVICENAME
# - $INSTALL_DIR
# - An user account with your name ($SERVICENAME)

# 1. TODO Install dependencies
# EXAMPLE: apt-get install -y nginx
apt-get update
apt-get install -y socat uuid-dev bindfs python3-ply

# 2. TODO Copy/move files
mv service/interpreter/main "$INSTALL_DIR/saarvm"
mv service/frontend/main "$INSTALL_DIR/frontend"
mkdir "$INSTALL_DIR/compiler"
mv service/compiler/compiler/*\.py "$INSTALL_DIR/compiler"
mv service/compiler/saascc "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/saascc"
mkdir "$INSTALL_DIR/data"
chown -R "$SERVICENAME:$SERVICENAME" "$INSTALL_DIR"

# 3. TODO Configure the server
# ...
# For example: 
# - adjust configs of related services (nginx/databases/...)
# - Build your service if there's source code on the box
# - ...
# 
# Useful commands:
# - nginx-location-add <<EOF
#   location {} # something you want to add to nginx default config (port 80)
#   EOF

make-append-only "$INSTALL_DIR/data"

# 4. TODO Configure startup for your service
# Typically use systemd for that:
# Install backend as systemd service
# Hint: you can use "service-add-simple '<command>' '<working directory>' '<description>'"
# service-add-simple "$INSTALL_DIR/TODO-your-script-that-should-be-started.sh" "$INSTALL_DIR/" "<TODO>"
service-add-simple "bash -c \"if [ ! -f \"server.pem\" ];then openssl genrsa -out \"server.key\"; openssl req -new -x509 -key \"server.key\" -subj '/CN=SaaSSaaSSaaSSaaS' -out \"server.crt\"; cat \"server.key\" \"server.crt\" > \"server.pem\";fi;socat -s -T10 OPENSSL-LISTEN:24929,reuseaddr,fork,verify=0,cert='server.pem' EXEC:'${INSTALL_DIR}/frontend',pty,stderr,setsid,sigint,sane\"" "$INSTALL_DIR/" "Saarsec alluring allegiant Superb Secure and absolutely Safe Speedy advanced arithmetic Stack System as a Service"

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
