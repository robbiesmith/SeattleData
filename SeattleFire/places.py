from geopy.geocoders import Nominatim, GoogleV3
from geopy.distance import vincenty
from geopy.location import Location
from geopy.point import Point
import re
from time import sleep
import pandas as pd
import datetime
from SeattleFire import cnxnMgr

def distanceFromDowntown(location):
    downtown = (47.6062, -122.3321)
    return vincenty((location.latitude, location.longitude), downtown).kilometers
    
def getLocationForAddress(address):
    address = address.replace(" / ", " & ") + " Seattle Washington"
    if re.search("[a-z] ?[/]", address.lower()):
        address = address.replace("/", " & ")
#    geolocator = Nominatim()
#    location = geolocator.geocode(address)
#    sleep(0.80) # don't get Nominatim mad at you
    location = None
    if location:
        if distanceFromDowntown(location) < 20:
            return location
        else:
            print ("osm too far")
    else:
        apikey = 'AIzaSyAW7T5d23BKVdf0hUB27p5MSa-dWhKnkUo' # only need api key during larger jobs - such as initial data load
        googlegeo = GoogleV3(api_key=apikey, timeout=3)
        location = googlegeo.geocode(address)
        if location:
            if distanceFromDowntown(location) < 20:
                return location
            else:
                print ("google too far")
    print("CANNOT FIND " + address)
    return None

def setLatLong(cursor):
    results = cursor.execute("select * from location where place is null").fetchall() # about 140,000 - fits in memory
    for row in results:
        if not row.place:
            freeways = ['sb i5', 'nb i5', 'sb sr99', 'nb sr99', 'wb sr520', 'eb sr520', 'wb i90', 'eb i90', 'eb wsea', 'wb wsea', 'nb sr509', 'sb sr509']
            if any(x in row.raw_location.lower() for x in freeways):
                continue
            try:
                location = getLocationForAddress(row.raw_location)
                if location:
                    cursor.execute("update location set place = geography::Point(?, ?, 4326) where id = ?", location.latitude, location.longitude, row.id)
                    cursor.commit()
            except Exception as e:
                print(e)
                print("SERVER ERROR " + row.raw_location)
        else:
            pass

#setLatLong(cursor)

def setStreet():
    cursor = cnxnMgr.getCursor()
# if place is not null
# if contains a space-slash-space then separate these two parts into street and cross street
# if starts with a number pull the number off and write the rest
    results = cursor.execute("select * from location where place is not null and street_name is null").fetchall() # about 140,000 max - fits in memory
#    results = cursor.execute("select * from location where raw_location like'%/%' and street_name is null").fetchall() # about 140,000 max - fits in memory
    for row in results:
        location = row.raw_location
        if re.search(" [/] ", location.lower()):
            parts = location.split("/")
            if len(parts) == 2:
                cursor.execute("update location set street_name = ?, cross_street = ? where id = ?", parts[0], parts[1], row.id)
                cursor.commit()
        elif re.search("[a-z] ?[/]", location.lower()):
            parts = location.split("/")
            if len(parts) == 2:
                cursor.execute("update location set street_name = ?, cross_street = ? where id = ?", parts[0], parts[1], row.id)
                cursor.commit()
        elif re.match("\d+ av[ e]", location.lower()):
            # if a numbered ave then it's not a house number
            pass
        elif re.match("\d+ ", location):
            parts = location.split(" ", 1)
            if len(parts) == 2:
                cursor.execute("update location set street_number = ?, street_name = ? where id = ?", parts[0], parts[1], row.id)
                cursor.commit()
        elif re.match("\d+-\d+ ", location):
            parts = location.split(" ", 1)
            if len(parts) == 2:
                numbers = parts[0].split("-", 1)
                if len(numbers) == 2:
                    cursor.execute("update location set street_number = ?, street_name = ? where id = ?", numbers[0], parts[1], row.id)
                    cursor.commit()
                
    results = cursor.execute("select * from location where place is not null and street_name like '- %'").fetchall()
    for row in results:
        street_name = row.street_name
        if re.match("- \d+ ", street_name):
            parts = street_name.split(" ", 2)
            if len(parts) == 3:
                cursor.execute("update location set street_name = ? where id = ?", parts[2], row.id)
                cursor.commit()

setStreet()

def checkForAv():
# one time method
    cursor = cnxnMgr.getCursor()
    results = cursor.execute("select * from location where place is not null and lower(street_name) like 'av%'").fetchall() # about 
    for row in results:
        location = row.raw_location
        if re.match("^\d+ av[ e//]", location.lower()):
            cursor.execute("update location set place = null, street_number = null, street_name = null, cross_street = null where id = ?", row.id)
            cursor.commit()
            print(location)
            print(row.street_name)
            print()

#checkForAv()

def removeTooFar(cursor):
    results = cursor.execute("DECLARE @loc AS geography = geography::Point(47.6062, -122.3321, 4326); SELECT * FROM location WHERE place is not null and location.place.STDistance(@loc) > 20000").fetchall() # about 140,000 - fits in memory
    for row in results:
        cursor.execute("update location set place = null, street_number = null, street_name = null, cross_street = null where id = ?", row.id)
        cursor.commit()
        
    cursor.commit()

def writeOfficialLocationIfMissing(date):
    return
# this method is dead
    formatted = date.strftime("%Y-%m-%d")
    print(formatted)
    url = "https://data.seattle.gov/resource/grwu-wqtk.json?$where=datetime+between+'" + formatted + "T00:00:00'+and+'" + formatted + "T23:59:59'"
    print(url)
    df = pd.read_json(url)
    for index, row in df.iterrows():

        incidentNum = row['incident_number']
        if not incidentNum or not hasattr(incidentNum, 'startswith') or not incidentNum.startswith('F1'):
            continue
        officialLat = row['latitude']
        officialLong = row['longitude']
        address = row['address']

        results = cursor.execute("select place, place.Lat, place.Long, location.raw_location, location.id from location inner join incident_location on incident_location.raw_location = location.raw_location where incident_location.incidentNumber = ?", incidentNum).fetchone()

        if results and not results[0] and officialLat and officialLong:
            try:
                loc = Location(point=Point(latitude=officialLat, longitude=officialLong))
                if distanceFromDowntown(loc) < 20:
                    print('write from official')
                    print()
                    cursor.execute("update location set place = geography::Point(?, ?, 4326) where id = ?", officialLat, officialLong, results[4])
                    cursor.commit()
            except (ValueError, UnboundLocalError):
                print('write error')
                print()
                continue

# looks like data.seattle only needs app token in unusual circumstances
# $$app_token = HdjmSRiVqTrizDSJd6FOUtWr9
# https://data.seattle.gov/resource/grwu-wqtk.json?$where=datetime between '2015-01-10T12:00:00' and '2015-01-10T14:00:00'

def checkLocationByDate(cursor, date):
# should do three things:
# make sure every address is close to the API address
# make sure every address is no more than 20 km from downtown
# if not write the API address

# https://data.seattle.gov/resource/grwu-wqtk.json?$where=incident_number+=+%27F170063119%27
    alreadyChecked = []
    formatted = date.strftime("%Y-%m-%d")
    print(formatted)
    url = "https://data.seattle.gov/resource/grwu-wqtk.json?$where=datetime+between+'" + formatted + "T00:00:00'+and+'" + formatted + "T23:59:59'"
    print(url)
    df = pd.read_json(url)
    for index, row in df.iterrows():
        incidentNum = row['incident_number']
        if not incidentNum or not hasattr(incidentNum, 'startswith') or not incidentNum.startswith('F1'):
            continue
        officialLat = row['latitude']
        officialLong = row['longitude']
        address = row['address']
        if address in alreadyChecked:
            continue
        else:
            alreadyChecked.append(address)

        try:
            address = address.replace(" / ", " & ") + " Seattle Washington"
        except AttributeError:
            continue

        results = cursor.execute("select place, place.Lat, place.Long, location.raw_location, location.id from location inner join incident_location on incident_location.raw_location = location.raw_location where incident_location.incidentNumber = ?", incidentNum).fetchone()

        if results and not results[0] and officialLat and officialLong:
            try:
                loc = Location(point=Point(latitude=officialLat, longitude=officialLong))
                if distanceFromDowntown(loc) < 20:
                    print('write from official - nothing in DB')
                    print(results[3])
                    print(incidentNum)
                    print()
                    cursor.execute("update location set place = geography::Point(?, ?, 4326) where id = ?", officialLat, officialLong, results[4])
                    cursor.commit()
            except (ValueError, UnboundLocalError):
                print('write error')
                print()
                continue
        elif results and results[0]:
            try:
                if vincenty((officialLat, officialLong), (results[1], results[2])).meters > 500:
                    print('in DB too far from official')
                    apikey = None
                    googlegeo = GoogleV3(api_key=apikey, timeout=3)
                    location = googlegeo.geocode(address)
                    if location and vincenty((officialLat, officialLong), (location.latitude, location.longitude)).meters < 500:
                        cursor.execute("update location set place = geography::Point(?, ?, 4326) where id = ?", location.latitude, location.longitude, results[4])
                        cursor.commit()
                        print('write from google')
                        print(address)
                        print(vincenty((officialLat, officialLong), (location.latitude, location.longitude)).meters)
                        print(incidentNum)
                        print()
                    else:
                        cursor.execute("update location set place = geography::Point(?, ?, 4326) where id = ?", officialLat, officialLong, results[4])
                        cursor.commit()
                        print('write from official - location too far from official')
                        print(officialLat)
                        print(officialLong)
                        print(results[3])
                        print(incidentNum)
                        print('google distance too far or missing:')
                        print(vincenty((officialLat, officialLong), (location.latitude, location.longitude)).meters)
                        print()

            except:
                print('write problem')
                print((officialLat, officialLong), (results[1], results[2]))
                print(results[3])
                print(incidentNum)
                print()
                continue
        

# select * from location inner join incident_location on incident_location.raw_location = location.raw_location where incident_location.incidentNumber = 'F170029705'