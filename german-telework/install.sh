#!/usr/bin/env bash

set -eux

# Install the service on a fresh vulnbox. Target should be /home/<servicename>
# You get:
# - $SERVICENAME
# - $INSTALL_DIR
# - An user account with your name ($SERVICENAME)

# 1. TODO Install dependencies
# EXAMPLE: apt-get install -y nginx
ls
pwd
# this broke literally overnight
wget http://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb

# wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
# chmod +x ./dotnet-install.sh
# ./dotnet-install.sh --version latest
# export DOTNET_ROOT=$HOME/.dotnet
# export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools
apt-get update
apt-get install -y socat fpc cmake default-jdk dotnet-sdk-7.0
dotnet --version

# 2. TODO Copy/move files
mv service/gateway "$INSTALL_DIR/"
mv service/router "$INSTALL_DIR/"
mv service/board "$INSTALL_DIR/"
mv service/holiday "$INSTALL_DIR/"
mv service/messagecrypt "$INSTALL_DIR/"
mv service/tasks "$INSTALL_DIR/"
/usr/lib/x86_64-linux-gnu/libc.so.6
# 3. TODO Configure the server
cd $INSTALL_DIR/board && make
cd $INSTALL_DIR/tasks && rm -f *.class && javac *.java
cd $INSTALL_DIR/holiday/Holiday && dotnet build --configuration Release 
cd $INSTALL_DIR/messagecrypt && mkdir build && cd build && cmake .. && make
/usr/lib/x86_64-linux-gnu/libc.so.6
chown -R "$SERVICENAME:$SERVICENAME" "$INSTALL_DIR"
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


# 4. TODO Configure startup for your service
# Typically use systemd for that:
# Install backend as systemd service
# Hint: you can use "service-add-simple '<command>' '<working directory>' '<description>'"
# service-add-simple "$INSTALL_DIR/TODO-your-script-that-should-be-started.sh" "$INSTALL_DIR/" "<TODO>"
service-add-simple "python3 -u gateway.py" "$INSTALL_DIR/gateway" "telework"
SERVICESUFFIX=-router service-add-simple "python3 router.py" "$INSTALL_DIR/router" "telework-router"
SERVICESUFFIX=-board service-add-simple "$INSTALL_DIR/board/build/board" "$INSTALL_DIR/board" "telework-board"
SERVICESUFFIX=-holiday service-add-simple "$INSTALL_DIR/holiday/Holiday/bin/Release/net7.0/Holiday" "$INSTALL_DIR/holiday/Holiday/bin/Release/net7.0" "telework-holiday"
SERVICESUFFIX=-task service-add-simple "java NetworkReceiver" "$INSTALL_DIR/tasks" "telework-tasks"
SERVICESUFFIX=-messagecrypt service-add-simple "$INSTALL_DIR/messagecrypt/build/messagecrypt" "$INSTALL_DIR/messagecrypt/build" "telework-messagecrypt"

# Example: Cronjob that removes stored files after a while
cronjob-add "*/6 * * * * find $INSTALL_DIR/gateway/data -mmin +45 -type f -delete"
cronjob-add "*/6 * * * * find $INSTALL_DIR/holiday/Holiday/data -mmin +45 -type f -delete"
cronjob-add "*/6 * * * * find $INSTALL_DIR/tasks/data -mmin +45 -type f -delete"
cronjob-add "*/6 * * * * find $INSTALL_DIR/board/data -mmin +45 -type f -delete"



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

# Cleanup
# terminate the dotnet build service (which keeps 20+ files in /tmp alive)
timeout 3 dotnet build-server shutdown || true

