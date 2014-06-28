#! /bin/bash

DB_NAME=data/ua_sensors.sqlite3
INSTALL_FOLDER=pcduino-installer-assets
CHART_DESKTOP_CONF=ua-sensors-charts.desktop
LOG_SERVICE=ua-sensors-logger
SERVER_SERVICE=ua-sensors-server

# Download dependencies
sudo apt-get update
sudo apt-get install ssh
sudo apt-get install vim
sudo apt-get install git-core
sudo apt-get install sqlite3
sudo apt-get install python-pip

sudo pip install —upgrade pip
sudo pip install -r requirements.txt

# Generate dummy data for demo
python dummy_data.py

# Create demo database using dummy dat
python csv_importer.py

# Create upstart services
sudo cp $INSTALL_FOLDER/$LOG_SERVICE.conf /etc/init/$LOG_SERVICE.conf
sudo cp $INSTALL_FOLDER/$SERVER_SERVICE.conf /etc/init/$SERVER_SERVICE.conf

# Create desktop menu item
sudo cp $INSTALL_FOLDER/$CHART_DESKTOP_CONF /usr/share/applications/$CHART_DESKTOP_CONF

# Start logger service
sudo start $LOG_SERVICE

# Start server service
sudo start $SERVER_SERVICE