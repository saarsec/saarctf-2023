#!/usr/bin/env bash

set -eux

# Install the service on a fresh vulnbox. Target should be /home/<servicename>
# You get:
# - $SERVICENAME
# - $INSTALL_DIR
# - An user account with your name ($SERVICENAME)

# 1. Install dependencies
apt-get update
# 1.1 Install SURY repository for old PHP (https://packages.sury.org/php/README.txt)
apt-get -y install lsb-release ca-certificates curl
curl -sSLo /usr/share/keyrings/deb.sury.org-php.gpg https://packages.sury.org/php/apt.gpg
rm -f /etc/apt/apt.conf.d/01proxy
echo "deb [signed-by=/usr/share/keyrings/deb.sury.org-php.gpg] https://packages.sury.org/php/ $(lsb_release -sc) main" > /etc/apt/sources.list.d/php.list
apt-get update
apt-get install -y nginx php7.4-fpm php7.4-mysqli php7.4-gd mariadb-server



# 2. Copy/move files
mv service/* "$INSTALL_DIR/"
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
cat - > /etc/nginx/sites-available/$SERVICENAME <<EOF
server {
    listen 8080;
    root $INSTALL_DIR;

    location / {
        index index.php;
        try_files \$uri \$uri/ =404;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/run/php/php7.4-fpm.sock;
        include fastcgi_params;
        fastcgi_param  SCRIPT_FILENAME  $INSTALL_DIR/\$fastcgi_script_name;
        fastcgi_param  SCRIPT_NAME  \$fastcgi_script_name;
    }

}
EOF

# Give nginx access rights on the homedir
usermod -aG $SERVICENAME www-data

ln -s /etc/nginx/sites-available/$SERVICENAME /etc/nginx/sites-enabled/$SERVICENAME

# 4. TODO Configure startup for your service
# Typically use systemd for that:
# Install backend as systemd service
# Hint: you can use "service-add-simple '<command>' '<working directory>' '<description>'"
# service-add-simple "$INSTALL_DIR/TODO-your-script-that-should-be-started.sh" "$INSTALL_DIR/" "<TODO>"
# service-add-simple "socat -s -T10 TCP-LISTEN:31337,reuseaddr,fork EXEC:bash,pty,stderr,setsid,sigint,sane" "$INSTALL_DIR/" "<TODO>"

# Example: Cronjob that removes stored files after a while
# cronjob-add "*/6 * * * * find $INSTALL_DIR/data -mmin +45 -type f -delete"

# Configure php-fpm
mkdir -p /etc/systemd/system/php7.4-fpm.service.d
cat > /etc/systemd/system/php7.4-fpm.service.d/override.conf <<'EOF'
[Service]
MemoryAccounting=true
MemoryMax=1024M
LimitNPROC=1024
EOF

# Example: Initialize Databases (PostgreSQL example)

# Example: 5. Startup database (CI DOCKER ONLY, not on vulnbox)
# if detect-docker; then
#     EXAMPLE for PostgreSQL: pg_ctlcluster 11 main start
# fi

if detect-docker; then
    # docker hack for PHP
    mkdir -p /run/php
    # docker hack for mariadb
    mkdir -p /run/mysqld
    chown mysql:mysql /run/mysqld
    /usr/sbin/mariadbd -u mysql &
    MARIADB_PID=$!
    while [ ! -e /run/mysqld/mysqld.sock ];
    do
        sleep .5 # give db time to start...
    done
fi

# Example: 6. Configure PostgreSQL
# cp $INSTALL_DIR/*.sql /tmp/
# sudo -u postgres psql -v ON_ERROR_STOP=1 -f "/tmp/init.sql"

mariadb <<"EOF"
CREATE USER 'www-data' IDENTIFIED VIA unix_socket;
CREATE DATABASE pasteable;
GRANT ALL ON pasteable.* TO 'www-data';
EOF

mv $INSTALL_DIR/*.sql /tmp/
sudo -u www-data mariadb pasteable < /tmp/pasteable.sql

# Example: 7 Stop services (CI DOCKER ONLY)
# if detect-docker; then
#     pg_ctlcluster 11 main stop
# fi
if detect-docker; then
    kill $MARIADB_PID
fi
