import twitter
from SeattleFire import config
from SeattleFire import cnxnMgr
import datetime
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys
import time
from datetime import timedelta

def addTweet(id, text, datetime):
    cursor = cnxnMgr.getCursor()
    cursor.execute("if not exists (select id from tweet where id = ?) insert into tweet(id, text, datetime) values (?, ?, ?)", id, id, text, datetime)
    cursor.commit()
    
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

api = twitter.Api(consumer_key=config.data['twitter_consumer'],
    consumer_secret=config.data['twitter_consumer_secret'],
    access_token_key=config.data['twitter_access'],
    access_token_secret=config.data['twitter_access_secret'])


    
def updateTweets():
    cursor = cnxnMgr.getCursor()
    cursor.execute("select top 1 id from tweet order by datetime desc")
    for row in cursor.fetchall():
        id = row[0]
        results = api.GetUserTimeline(screen_name="SeattleFire",count=200,since_id=id)
        for r in results:
            d = datetime.datetime.strptime( r.created_at, "%a %b %d %H:%M:%S %z %Y" )
            u = utc_to_local(d)
            addTweet(r.id, r.text, u)
            print(r.id)

def longest_common_substring(s1, s2):
   m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
   longest, x_longest = 0, 0
   for x in range(1, 1 + len(s1)):
       for y in range(1, 1 + len(s2)):
           if s1[x - 1] == s2[y - 1]:
               m[x][y] = m[x - 1][y - 1] + 1
               if m[x][y] > longest:
                   longest = m[x][y]
                   x_longest = x
           else:
               m[x][y] = 0
   return s1[x_longest - longest: x_longest]
   
def assignIncidentToTweet(incidentNumber, tweetId):
    cursor = cnxnMgr.getCursor()
    cursor.execute("update tweet set incidentNumber = ? where id = ?", incidentNumber, tweetId)
    cursor.commit()
    
def getFirstStreetContentWord(streetName):
    words = streetName.split()
    remove = ['e','n','s','w','ne','se','nw','sw','st','av','west','east','north','south']
    words = [ x for x in words if len(x)>1 ]
    words = [ x for x in words if x.lower() not in remove ]
    return(words[0])
    
def removeIncidentFromTweet(tweetId):
    cursor = cnxnMgr.getCursor()
    cursor.execute("update tweet set incidentNumber = NULL where id = ?", tweetId)
    cursor.commit()
        
def lookForFalseMatches():
    cursor = cnxnMgr.getCursor()
    cursor.execute("select id, datetime, text, incidentNumber from tweet where incidentNumber is not null")
    for tweet in cursor.fetchall():
        for incident in cursor.execute("""
        select incident.number, incident.datetime, IT.raw_type, location.raw_location, location.street_number, location.street_name, location.cross_street from incident
        inner join incident_type as IT on incident.number = IT.incidentNumber
        inner join incident_location as IL on incident.number = IL.incidentNumber
        inner join location on IL.raw_location = location.raw_location
        where incident.number = ?
        """, tweet[3]):
            # pretty good check, but still misses typos in tweets like Genesse/Genesee or abbrevs Lk Wash/Lake Washington
            if not getFirstStreetContentWord(incident[5]).lower() in tweet[2].lower():
                print(tweet[2])
                print(incident[3])
                print(incident[2])
                print(getFirstStreetContentWord(incident[5]))
                removeIncidentFromTweet(tweet[0])
                break
        
def findIncidentForTweet(tweetId):
    cursor = cnxnMgr.getCursor()
    seen = []
    cursor.execute("select id, datetime, text from tweet where incidentNumber is null")
    for tweet in cursor.fetchall():
        lower = tweet[1] + timedelta(hours=-24)
        upper = tweet[1] + timedelta(hours=1)
        for incident in cursor.execute("""
        select incident.number, incident.datetime, IT.raw_type, IU.unit_name, location.raw_location, location.street_number, location.street_name, location.cross_street from incident
        inner join incident_type as IT on incident.number = IT.incidentNumber
        inner join incident_location as IL on incident.number = IL.incidentNumber
        inner join incident_unit as IU on incident.number = IU.incidentNumber
        inner join location on IL.raw_location = location.raw_location
        where incident.datetime between ? and ?
        """, lower, upper):
        # if house number and 5 char of street name in tweet
            if not incident[0] in seen and incident[5] and len(incident[5]) > 1 and incident[5] + ' ' in tweet[2] and incident[6] and getFirstStreetContentWord(incident[6]).lower() in tweet[2].lower().split():
                print(incident[2])
                print(incident[4])
                print(tweet[2])
                print()
                seen.append(incident[0])
                assignIncidentToTweet(incident[0], tweet[0])
                break
        continue
        for incident in cursor.execute("""
        select incident.number, incident.datetime, IT.raw_type, IU.unit_name, location.raw_location, location.street_number, location.street_name, location.cross_street from incident
        inner join incident_type as IT on incident.number = IT.incidentNumber
        inner join incident_location as IL on incident.number = IL.incidentNumber
        inner join incident_unit as IU on incident.number = IU.incidentNumber
        inner join location on IL.raw_location = location.raw_location
        where incident.datetime between ? and ?
        """, lower, upper):
        # if both the street and the cross street are in the tweet text based on distinct words
            if not incident[0] in seen and incident[6] and incident[7] and getFirstStreetContentWord(incident[6]).lower() in tweet[2].lower().split() and getFirstStreetContentWord(incident[7]).lower() in tweet[2].lower().split():
#                if incident[5] + ' ' in tweet[2]:
                print(incident[2])
                print(incident[4])
                print(tweet[2])
                print()
                seen.append(incident[0])
                assignIncidentToTweet(incident[0], tweet[0])
                break
        continue
        for incident in cursor.execute("""
        select incident.number, incident.datetime, IT.raw_type, IU.unit_name, location.raw_location, location.street_number, location.street_name, location.cross_street from incident
        inner join incident_type as IT on incident.number = IT.incidentNumber
        inner join incident_location as IL on incident.number = IL.incidentNumber
        inner join incident_unit as IU on incident.number = IU.incidentNumber
        inner join location on IL.raw_location = location.raw_location
        where incident.datetime between ? and ?
        """, lower, upper):
        # if both the street and the cross street are in the tweet text based on longest substring
            if not incident[0] in seen and incident[6] and len(longest_common_substring(incident[6], tweet[2])) > 4 and incident[7] and len(longest_common_substring(incident[7], tweet[2])) > 4:
#                if incident[5] + ' ' in tweet[2]:
                print(incident[2])
                print(incident[4])
                print(tweet[2])
                seen.append(incident[0])
                assignIncidentToTweet(incident[0], tweet[0])
                break
        for incident in cursor.execute("""
        select incident.number, incident.datetime, IT.raw_type, IU.unit_name, location.raw_location, location.street_number, location.street_name, location.cross_street from incident
        inner join incident_type as IT on incident.number = IT.incidentNumber
        inner join incident_location as IL on incident.number = IL.incidentNumber
        inner join incident_unit as IU on incident.number = IU.incidentNumber
        inner join location on IL.raw_location = location.raw_location
        where incident.datetime between ? and ?
        and IU.unit_name = 'PIO'
        """, lower, upper):
        # since this is an incident the PIO responded to then we should be biased twoard accepting it
            if not incident[0] in seen and incident[6] and len(longest_common_substring(incident[6], tweet[2])) > 4:
#                if incident[5] + ' ' in tweet[2]:
                print(incident[4])
                print(tweet[2])
                seen.append(incident[0])
#                assignIncidentToTweet(incident[0], tweet[0])
                break
        for incident in cursor.execute("""
        select incident.number, incident.datetime, IT.raw_type, IU.unit_name, location.raw_location, location.street_number, location.street_name, location.cross_street from incident
        inner join incident_type as IT on incident.number = IT.incidentNumber
        inner join incident_location as IL on incident.number = IL.incidentNumber
        inner join incident_unit as IU on incident.number = IU.incidentNumber
        inner join location on IL.raw_location = location.raw_location
        where incident.datetime between ? and ?
        """, lower, upper):
        # if house number and 5 char of street name in tweet
            if not incident[0] in seen and incident[5] and len(incident[5]) > 1 and incident[6] and len(longest_common_substring(incident[6], tweet[2])) > 4:
                if incident[5] + ' ' in tweet[2]:
                    print(incident[4])
                    print(tweet[2])
                    seen.append(incident[0])
                    assignIncidentToTweet(incident[0], tweet[0])
                    break
    print(len(seen))


    # get timestamp on tweet
    # look for incident that happened before it up to a few hours (and watch out for daylight savings)
    # see if street name is in tweet
    # see if other keywords (fire, vehicle, ...) are in tweet
    # watch for incidents that generate multiple tweets
    # watch for posts that link to the blog and expand the search timeline - espeically ones that have mutiple tweets already
    
    pass
    
def getAllTweets():
    # one-time method to get all tweets (limited to 3200 due to Twitter API limit)
    min_id_seen = None
    while True:
        results = api.GetUserTimeline(screen_name="SeattleFire",count=200,max_id=min_id_seen)

        for r in results:
            d = datetime.datetime.strptime( r.created_at, "%a %b %d %H:%M:%S %z %Y" )
            u = utc_to_local(d)
            addTweet(r.id, r.text, u)
            min_id_seen = r.id
            print(min_id_seen)
    
def getOldTweets():
    # one-time method to capture tweets older than 3200
    try:
        driver = webdriver.Chrome()
# start date based on observed existing minimum
#        driver.get('https://twitter.com/search?l=&q=from%3ASeattleFire%20until%3A2013-04-04&src=typd&lang=en')
        driver.get('https://twitter.com/search?l=&q=from%3ASeattleFire%20until%3A2010-06-08&src=typd&lang=en')
        time.sleep(2)
        for _ in range(20):
            driver.find_element_by_tag_name("body").send_keys(Keys.END)
            time.sleep(2)
        holders = driver.find_elements_by_xpath("//*[contains(@id,'stream-item-tweet-')]")
        for h in holders:
            id = h.get_attribute("id").replace("stream-item-tweet-", "")
            text = h.find_element_by_class_name("tweet-text").text
            timeVal = h.find_element_by_class_name("tweet-timestamp").get_attribute("title")
            d = datetime.datetime.strptime( timeVal, "%I:%M %p - %d %b %Y" )
            addTweet(int(id), text[:200], d)
        time.sleep(2)
        driver.close()

    except Exception as e:
        print(e)
    
#getAllTweets()

#getOldTweets()

#updateTweets()

findIncidentForTweet(None)

#lookForFalseMatches()