from lxml import etree
from datetime import timedelta, date
import urllib.parse
import places
import twitterCollector
from SeattleFire import config
from SeattleFire import cnxnMgr
import time


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


def writeIncident(cursor, incidentId, datetime, level):
    cursor.execute("if not exists (select number from incident where number = ?) insert into incident(number, datetime, level) values (?, ?, ?)", incidentId, incidentId, datetime, level)
    cursor.commit()

def writeUnits(cursor, units):
    for unit in units.split():
        cursor.execute("if not exists (select name from unit where name = ?) insert into unit(name) values (?)", unit, unit)
        cursor.commit()

def writeType(cursor, type):
    cursor.execute("if not exists (select raw_type from type where raw_type = ?) insert into type(raw_type) values (?)", type, type)
    cursor.commit()
    
def doesLocationExist(cursor, location):
    for row in cursor.execute("select id from location where raw_location = ?", location):
        return True
    return False
    
def writeLocation(cursor, location, loc):
    if loc:
        cursor.execute("if not exists (select raw_location from location where raw_location = ?) insert into location(raw_location, place) values (?, geography::Point(?, ?, 4326))", location, location, loc.latitude, loc.longitude)
        cursor.commit()
    else:
        cursor.execute("if not exists (select raw_location from location where raw_location = ?) insert into location(raw_location) values (?)", location, location)
        cursor.commit()
    
def writeIncidentType(cursor, incidentId, type):
    cursor.execute("if not exists (select incidentNumber from incident_type where incidentNumber = ? and raw_type = ?) insert into incident_type(incidentNumber, raw_type) values (?, ?)", incidentId, type, incidentId, type)
    cursor.commit()
    
def writeIncidentLocation(cursor, incidentId, location):
    cursor.execute("if not exists (select incidentNumber from incident_location where incidentNumber = ? and raw_location = ?) insert into incident_location(incidentNumber, raw_location) values (?, ?)", incidentId, location, incidentId, location)
    cursor.commit()
    
def writeIncidentUnits(cursor, incidentId, units):
    for unit in units.split():
        cursor.execute("if not exists (select incidentNumber from incident_unit where incidentNumber = ? and unit_name = ?) insert into incident_unit(incidentNumber, unit_name) values (?, ?)", incidentId, unit, incidentId, unit)
        cursor.commit()

def initialProcessForIncident(incidentId, datetime, level, units, location, type):
    cursor = cnxnMgr.getCursor()
    writeIncident(cursor, incidentId, datetime, level)
    if units:
        writeUnits(cursor, units)
        writeIncidentUnits(cursor, incidentId, units)
    if type:
        writeType(cursor, type)
        writeIncidentType(cursor, incidentId, type)
    if location:
        if not doesLocationExist(cursor, location):
            loc = places.getLocationForAddress(location)
            writeLocation(cursor, location, loc)
            # split street names & numbers
        writeIncidentLocation(cursor, incidentId, location)
        
        
def getOriginalDataForDate(single_date):
    cursor = cnxnMgr.getCursor()
    dateString = single_date.strftime("%m/%d/%Y")
    params = urllib.parse.urlencode( {"incDate": dateString, "rad1": "des" } )
    url = "http://www2.seattle.gov/fire/realtime911/getRecsForDatePub.asp?" + params
    print (url)

    parser = etree.HTMLParser()
    tree = etree.parse(url, parser)
    root = tree.getroot()

    incidentRows = tree.xpath("//tr[@id]") # all table rows with id defined
    for incidentRow in reversed(incidentRows):
        item = incidentRow.xpath("td")
        datetime = item[0].text;
        incidentId = item[1].text;
        try:
            level = int(item[2].text);
        except:
            level = 1
        units = item[3].text;
        location = item[4].text;
        type = item[5].text;
        print(incidentId)
        if not incidentId: # bad row - no idea what to do
            continue
        initialProcessForIncident(incidentId, datetime, level, units, location, type)
    # match tweets for date
    
def readRawData():
    twitterCollector.updateTweets()
    # read all tweets since last one
    cursor = cnxnMgr.getCursor()
    cursor.execute("select top 1 datetime from incident order by datetime desc")

#    start_date = date(2003, 11, 7) - data start
#    start_date = date(2017, 7, 17) # restart - run Jul 1
    for row in cursor.fetchall():
        start_date = (row[0] + timedelta(hours=1)).date()
        break
    end_date = date.today()
    for single_date in daterange(start_date, end_date):
        getOriginalDataForDate(single_date)
        places.checkLocationByDate(cursor, single_date)
        
    twitterCollector.findIncidentsForAllTweets()
    


def backfill():
    cursor = cnxnMgr.getCursor()
    
    start_date = date(2017, 6, 15) # need to run backfill for june 18
    end_date = date.today()
    for single_date in daterange(start_date, end_date):
        print(single_date)
        places.checkLocationByDate(cursor, single_date)

if __name__ == "__main__":
    while True:
        readRawData()
        time.sleep(86400)

#backfill()

# readRawData
# backfill
# updateTweets
# matchtweetstoIncidents
# on 24 cycle with logging and error tolerance