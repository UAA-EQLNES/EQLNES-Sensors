#! /bin/bash

DB_NAME=data/ua_sensors.sqlite3
INSTALL_FOLDER=pcduino-installer-assets
LOG_CONF=ua-sensors-logger.conf
SERVER_CONF=ua-sensors-server.conf
CHART_DESKTOP_CONF=ua-sensors-charts.desktop

# Download dependencies
sudo apt-get update
sudo apt-get install ssh
sudo apt-get install vim
sudo apt-get install git-core
sudo apt-get install sqlite3
sudo apt-get install python-pip

sudo pip install —upgrade pip
sudo pip install -r requirements.txt
sudo pip install flask
sudo pip install pyserial
sudo pip install flask-assets
sudo pip install cssmin

# Create Database
sqlite3 $DB_NAME

# Create upstart services
sudo cp $INSTALL_FOLDER/$LOG_CONF /etc/init/$LOG_CONF
sudo cp $INSTALL_FOLDER/$SERVER_CONF /etc/init/$SERVER_CONF

# Create desktop menu item
sudp cp $INSTALL_FOLDER/$CHART_DESKTOP_CONF /usr/share/applications/$CHART_DESKTOP_CONF