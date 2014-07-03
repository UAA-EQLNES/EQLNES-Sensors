from datetime import datetime, timedelta
import json
import sqlite3

from flask import Flask, Response, request, render_template
from flask_assets import Environment, Bundle

from core import SensorReadingsDataStore


# Helper functions
def build_sensors_options(sensors, sensor_names):
    sensor_options = []
    for sensor_id in sensors:
        sensor_options.append((
            sensor_id,
            sensor_names.get(sensor_id, sensor_id)))
    return tuple(sensor_options)


def calculate_date_range(days=7, format="%m/%d/%Y"):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return (start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y"))


def read_log_file():
    with open(app.config['DATA_LOGGER_ERROR_FILE'], 'r') as f:
        f.seek (0, 2)
        fsize = f.tell()
        f.seek (max (fsize-5120, 0), 0)
        lines = f.readlines()
    log_lines = [line.strip() for line in lines if len(line.strip()) > 0]
    log = []
    current_line = None
    for line in log_lines:
        if line.startswith('INFO') or line.startswith('ERROR'):
            if current_line is not None:
                if current_line.startswith('ERROR'):
                    log.append(('danger', current_line))
                else:
                    log.append(('default', current_line))
            current_line = line
        elif current_line is not None:
            current_line += line
    log.reverse()
    return log


# Create web server and load settings
app = Flask(__name__, static_url_path='')
app.config.from_object('default_settings')
app.config.from_pyfile('settings.cfg', silent=True)


# Assets plugin creates optimized javascript and css files
# to improve page load a bit
assets = Environment(app)
assets.versions = 'timestamp'


# Optimize Main javascript files
js_assets = Bundle(
    'vendor/js/jquery.js',
    'vendor/js/jquery.flot.js',
    'vendor/js/jquery.flot.axislabels.js',
    'vendor/js/jquery.flot.time.js',
    'vendor/js/jquery.flot.tooltip.js',
    'vendor/js/jquery.flot.downsample.js',
    'vendor/js/select2.js',
    'vendor/js/bootstrap-button.js',
    'vendor/js/bootstrap-datepicker.js',
    filters='rjsmin',
    output='js/min.js')
assets.register('js_all', js_assets)

# Optimize Log javascript files
js_log_assets = Bundle(
    'vendor/js/jquery.js',
    filters='rjsmin',
    output='js/jquery.min.js')
assets.register('js_log', js_log_assets)


# Optimize CSS files
css_assets = Bundle(
    'vendor/css/bootstrap.css',
    'vendor/css/bootstrap-datepicker.css',
    'vendor/css/select2.css',
    'vendor/css/select2-bootstrap.css',
    filters='cssmin',
    output='css/min.css'
)
assets.register('css_all', css_assets)


# Initialize class to query database
db = SensorReadingsDataStore(app.config['SQLITE3_DB_PATH'])
db.setup()

# Main home page
@app.route('/')
def root():
    sensors = db.fetch_sensors()
    sensor_options = build_sensors_options(sensors, app.config.get('SENSOR_NAMES', {}))
    start_date, end_date = calculate_date_range()
    data = db.fetch(sensors[0], start_date, end_date)
    json_data = json.dumps(data)
    return render_template(
        app.config['TEMPLATE'],
        site_title=app.config['SITE_TITLE'],
        refresh_interval=app.config['REFRESH_INTERVAL'],
        sensor_options=sensor_options,
        start_date=start_date,
        end_date=end_date,
        data=json_data,)

@app.route('/status')
def show_status():
    return render_template('status.html',
        site_title=app.config['SITE_TITLE'],
        refresh_interval=app.config['REFRESH_INTERVAL'],
        log=read_log_file())


# Endpoint to retrieve data in JSON format
@app.route('/api/data', methods=['GET'])
def fetch_data():
    sensor = request.args.get('sensor', None)
    start_date = request.args.get('start-date', None)
    end_date = request.args.get('end-date', None)
    data = db.fetch(sensor, start_date, end_date)
    return Response(json.dumps(data), mimetype='application/json')


# Endpoint to retrieve log data in JSON format
@app.route('/api/status', methods=['GET'])
def fetch_status():
    return render_template('log_table.html', log=read_log_file())


# If file is run directly - ie. python server.py - then start server
if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'])
