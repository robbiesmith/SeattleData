import re
from datetime import date
from SeattleFire.cnxnMgr import getCursor

def isFloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
        
def getIncidents(units=[], types=[], locations=[], region="", dateRange=()):
    types = set(types) # remove duplicates
    cursor = getCursor()
    # uses AND for the list of units, but OR for other lists
    # only a single region or daterange accepted

    unitstring = ""
    for unit in units:
        dbName = "iu" + unit
        unitstring += "inner join incident_unit as " + dbName + " on incident.number = " + dbName + ".incidentNumber and " + dbName + ".unit_name = '" + unit + "' "
    type = "IT.raw_type in ('" + "\',\'".join([t.replace("'", "''") for t in types]) + "')" if types else '1=1'
    location = "IL.raw_location in ('" + "\',\'".join(locations) + "')" if locations else '1=1'
    
    geoPrefix = ""
    geoBody = "1=1"
    if region:
        parts = region.split(",")
        if len(parts) == 4 and all(isFloat(i) for i in parts):
            lats = (parts[0], parts[2])
            longs = (parts[1], parts[3])
#        lats = (region[0][0], region[1][0])
#        longs =  (region[0][1], region[1][1])
#        geoPrefix = "DECLARE @g geography; SET @g = geography::STPolyFromText('POLYGON((-122.301 47.671, -122.278 47.671, -122.278 47.675, -122.301 47.675, -122.301 47.671))', 4326);"
            geoPrefix = "DECLARE @g geography; SET @g = geography::STPolyFromText('POLYGON(({2} {0}, {2} {1}, {3} {1}, {3} {0}, {2} {0}))', 4326);".format(min(lats), max(lats), min(longs), max(longs))
            geoBody = "@g.STContains(location.place) = 1"
    date = "1=1"
    if dateRange:
        date = "incident.datetime between '" + dateRange[0].isoformat() + "' and '" + dateRange[1].isoformat() + "'"

    output = {"incident":{}, "display":"all", "totals":{"type":{}, "unit":{}, "weekday":[0]*7, "month":[0]*13, "hour":[0]*24, "year":{}}} # note: month zero will never happen - one-based

    print("""
        {}
        select incident.number, incident.datetime, location.place.Lat, location.place.Long, IT.raw_type, IU.unit_name, incident.raw_location from incident
        {}
        inner join incident_type as IT on incident.number = IT.incidentNumber
        inner join incident_location as IL on incident.number = IL.incidentNumber
        inner join incident_unit as IU on incident.number = IU.incidentNumber
        inner join location on IL.raw_location = location.raw_location
        where
        {}
        and  {}
        and  {}
        and  {}
        """.format(
        geoPrefix,
        unitstring,
        type,
        location,
        geoBody,
        date
        ))
    fullDataLimit = 250
    partialDataLimit = 10000
    i = 0
    for row in cursor.execute("""
        {}
        select incident.number, incident.datetime, location.place.Lat, location.place.Long, IT.raw_type, IU.unit_name, location.raw_location from incident
        {}
        inner join incident_type as IT on incident.number = IT.incidentNumber
        inner join incident_location as IL on incident.number = IL.incidentNumber
        inner join incident_unit as IU on incident.number = IU.incidentNumber
        inner join location on IL.raw_location = location.raw_location
        where
        {}
        and  {}
        and  {}
        and  {}
        """.format(
        geoPrefix,
        unitstring,
        type,
        location,
        geoBody,
        date
        )):
# for up to N return full data
# for up to M return only lat/long
# for more tham M randomly replace data so that a total of M items is returned
        incidentNumber = row[0]
        incidentDateTime = row[1]
        incidentLat = row[2]
        incidentLong = row[3]
        incidentType = row[4]
        incidentUnit = row[5]
        rawLocation = row[6]
        if not incidentNumber in output["incident"]:
            if i < partialDataLimit:
                if i < fullDataLimit:
                    output["incident"][incidentNumber] = {"type":incidentType, "unit":[incidentUnit], "location":(incidentLat, incidentLong), "datetime":incidentDateTime, "rawLocation":rawLocation}
                else:
                    output["incident"][incidentNumber] = {"location":(incidentLat, incidentLong)}

            if not incidentType in output["totals"]["type"]:
                output["totals"]["type"][incidentType] = 1
            else:
                output["totals"]["type"][incidentType] += 1

            if not incidentDateTime.year in output["totals"]["year"]:
                output["totals"]["year"][incidentDateTime.year] = 1
            else:
                output["totals"]["year"][incidentDateTime.year] += 1
            output["totals"]["hour"][incidentDateTime.hour] += 1
            output["totals"]["month"][incidentDateTime.month] += 1 # note: using 1-based months
            output["totals"]["weekday"][incidentDateTime.weekday()] += 1

            i += 1 # count distinct incidents to determine display type
        else:
            if i < fullDataLimit:
                output["incident"][incidentNumber]["unit"].append(incidentUnit)

        if not incidentUnit in output["totals"]["unit"]:
            output["totals"]["unit"][incidentUnit] = 1
        else:
            output["totals"]["unit"][incidentUnit] +=1

    if i > fullDataLimit:
        output["display"] = "heatmap"

    return output

# get incidents by region
# get incidents by named street
# get incidents by day of week, month, hour of day, time period
# for a list of incidents get lat/long
# for a list of incidents get times, include day of week, hour of day, month, year
# for a list of incidents get types
# for a list of incidents get units

print('queries initialized')
#x = getIncidents(region=((47.671, -122.301), (47.675, -122.278)), dateRange=(date(2016, 1, 1), date.today()))
#x = getIncidents([], [], [], ((47.671, -122.301), (47.675, -122.278)), (date(2016, 1, 1), date.today()))
#x = getIncidents([], [], [], (), (date(2004, 1, 1), date.today()))
#print(x)
#getIncidents(['E38'], [], ['4800 Sand Point Way Ne'], (), (date(2008, 1, 1), date.today()))
#getIncidents(['E40','M16','E38'], ['Aid Response','Medic Response','Fire in Building'], ['4800 Sand Point Way Ne','5739 33rd Av Ne'], ((47.671, -122.301), (47.675, -122.278)), ('10Jan2016', '14Jan2017'))
