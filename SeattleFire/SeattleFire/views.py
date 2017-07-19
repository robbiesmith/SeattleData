"""
Routes and views for the flask application.
"""



from datetime import datetime
from flask import render_template, Response, request, send_from_directory
from SeattleFire import app
from json import dumps
from SeattleFire.units import allunits
from SeattleFire.eventtypes import alltypes
from SeattleFire.cnxnMgr import getCursor
from SeattleFire.queries import getIncidents
from SeattleFire.detail import getDetail
import traceback

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")

@app.route('/')
@app.route("/map")
def map():
    return send_from_directory('static', 'map.html')


@app.route("/units")
def units():
    resp = Response(dumps(allunits()), mimetype="application/json")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp        

@app.route("/types")
def types():
    resp = Response(dumps(alltypes()), mimetype="application/json")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/detail")
def detail():
    args = request.args
    numbers = args.getlist('number')

    output = dumps(getDetail(numbers), default=json_serial)

    resp = Response(output, mimetype="application/json")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/query")
def query():
    args = request.args
    unit = args.getlist('unit')
    type = args.getlist('type')
    location = args.getlist('location')
    region = args.get('region', "")
    startdate = args.get('startdate', "2001-01-01")
    enddate = args.get('enddate', "2030-01-01")

    startdate = datetime.strptime(startdate,"%Y-%m-%d")
    enddate = datetime.strptime(enddate,"%Y-%m-%d").replace(hour=23, minute=59, second=59)
    # clean data input - reject all data if not in approved list
    if not set(type).issubset(alltypes()):
        type = []
    if not set(unit).issubset(allunits()):
        unit = []
    # the check for elements of region happens in queries.py
    # TODO: need to check the elements of location
    location = [] # just block location for now
    # no need to check dateRange - since converted to dates prevents SQL injection
    for retry in range(3):
        try:
            output = dumps(getIncidents(units=unit, types=type, locations=location, region=region, dateRange=(startdate,enddate)), default=json_serial)
            break
        except:
            output = "{}"
            cursor = getCursor(forced=True)
            traceback.print_exc()


    resp = Response(output, mimetype="application/json")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
