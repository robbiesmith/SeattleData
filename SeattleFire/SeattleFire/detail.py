from SeattleFire.cnxnMgr import getCursor

def getDetail(itemNumbers):
    output = []
    cursor = getCursor()

    for itemNumber in itemNumbers:
        outputItem = {"unit":[]}
        
        for row in cursor.execute("""
            select incident.number, incident.datetime, location.place.Lat, location.place.Long, IT.raw_type, IU.unit_name, location.raw_location from incident
            inner join incident_type as IT on incident.number = IT.incidentNumber
            inner join incident_location as IL on incident.number = IL.incidentNumber
            inner join incident_unit as IU on incident.number = IU.incidentNumber
            inner join location on IL.raw_location = location.raw_location
            where
            incident.number = ?
            """, itemNumber
            ):
            incidentNumber = row[0]
            incidentDateTime = row[1]
            incidentLat = row[2]
            incidentLong = row[3]
            incidentType = row[4]
            incidentUnit = row[5]
            rawLocation = row[6]
            outputItem["number"] = incidentNumber
            outputItem["location"] = (incidentLat, incidentLong)
            outputItem["datetime"] = incidentDateTime
            outputItem["type"] = incidentType
            outputItem["rawlocation"] = rawLocation
            outputItem["unit"].append(incidentUnit)

        output.append(outputItem)

    return output