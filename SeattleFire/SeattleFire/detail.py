from SeattleFire.cnxnMgr import getCursor

def getDetail(itemNumbers):
    output = {}
    cursor = getCursor()

    for row in cursor.execute("""
        select incident.number, incident.datetime, location.place.Lat, location.place.Long, IT.raw_type, IU.unit_name, location.raw_location from incident
        inner join incident_type as IT on incident.number = IT.incidentNumber
        inner join incident_location as IL on incident.number = IL.incidentNumber
        inner join incident_unit as IU on incident.number = IU.incidentNumber
        inner join location on IL.raw_location = location.raw_location
        where
        incident.number in (?)
        """, "%s" % "\",\"".join(itemNumbers)
        ):
        incidentNumber = row[0]
        incidentDateTime = row[1]
        incidentLat = row[2]
        incidentLong = row[3]
        incidentType = row[4]
        incidentUnit = row[5]
        rawLocation = row[6]
        if not incidentNumber in output:
            output[incidentNumber] = {"unit":[]}
            output[incidentNumber]["number"] = incidentNumber
            output[incidentNumber]["location"] = (incidentLat, incidentLong)
            output[incidentNumber]["datetime"] = incidentDateTime
            output[incidentNumber]["type"] = incidentType
            output[incidentNumber]["rawlocation"] = rawLocation
        output[incidentNumber]["unit"].append(incidentUnit)

    return output