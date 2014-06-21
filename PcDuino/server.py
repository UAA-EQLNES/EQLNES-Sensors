import json
import sqlite3

from flask import Flask, Response, request, render_template
from flask_assets import Environment, Bundle

from core import SensorReadingsDataStore


# Create web server and load settings
app = Flask(__name__, static_url_path='')
app.config.from_object('default_settings')
app.config.from_pyfile('settings.cfg', silent=True)

# Assets plugin creates optimized javascript and css files
# to improve page load a bit
assets = Environment(app)
assets.versions = 'timestamp'

# Optimize Javascript files
js_assets = Bundle(
    'vendor/js/jquery.js',
    'vendor/js/jquery.flot.js',
    'vendor/js/jquery.flot.resize.js',
    'vendor/js/jquery.flot.axislabels.js',
    'vendor/js/jquery.flot.time.js',
    'vendor/js/jquery.flot.tooltip.js',
    'vendor/js/select2.js',
    'vendor/js/bootstrap-datepicker.js',
    filters='rjsmin',
    output='js/min.js')
assets.register('js_all', js_assets)

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

# Main home page
@app.route('/')
def root():
    sensors = db.fetch_sensors()
    data = db.fetch(sensors[0])
    json_data = json.dumps(data)
    return render_template(app.config['TEMPLATE'], sensors=sensors, data=json_data)

# Endpoint to retrieve data in JSON format
@app.route('/api/data', methods=['GET'])
def fetch_data():
    sensor = request.args.get('sensor', None)
    start_date = request.args.get('start-date', None)
    end_date = request.args.get('end-date', None)
    data = db.fetch(sensor, start_date, end_date)
    return Response(json.dumps(data), mimetype='application/json')

# If file is run directly - ie. python server.py - then start server
if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'])
