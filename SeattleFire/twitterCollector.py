import twitter
from SeattleFire import config
from SeattleFire import cnxnMgr
import datetime
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys
import time

def addTweet(id, text, datetime):
    cursor = cnxnMgr.getCursor()
    cursor.execute("if not exists (select id from tweet where id = ?) insert into tweet(id, text, datetime) values (?, ?, ?)", id, id, text, datetime)
    cursor.commit()
    
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

api = twitter.Api(consumer_key='T4x607ZBXKERs5I7Cmf97BY8D',
    consumer_secret='kbUwTTtRinMV2gG4k7ms6cDXdJQcFwRThGl9PL2G7sfObpHDbD',
    access_token_key='2270889487-D6OFqCnJadvfLqUVYhgnPBd9vi8c4gejdVPcNQN',
    access_token_secret='o69GvXZXQnfQFqbfXvrbBX2Hfb1vbmopRtdClMi0dJtsd')

min_id_seen = None
#min_id_seen = 319794050385461248


#    addTweet(r.id, r.text, r.created_at)
def getAllTweets():
    global min_id_seen
    while True:
        results = api.GetUserTimeline(screen_name="SeattleFire",count=2,max_id=min_id_seen)

        for r in results:
            d = datetime.datetime.strptime( r.created_at, "%a %b %d %H:%M:%S %z %Y" )
            u = utc_to_local(d)
            addTweet(r.id, r.text, u)
            min_id_seen = r.id
            print(min_id_seen)
    # find newest tweet in DB
    # stop when find a tweet already in DB
#results = api.GetUserTimeline(screen_name="SeattleFire",count=200,max_id=836296897451085829)

    # would using search expand the timeline?
    # would using web scraping expand the timeline?
    
def updateTweets():
    # find newest tweet - use as since_id 
    # from there keep going until no more
    results = api.GetUserTimeline(screen_name="SeattleFire",count=200,since_id=836296897451085829)

def findIncidentForTweet(tweetId):
    # get timestamp on tweet
    # look for incident that happened before it up to a few hours (and watch out for daylight savings)
    # see if street name is in tweet
    # see if other keywords (fire, vehicle, ...) are in tweet
    # watch for incidents that generate multiple tweets
    # watch for posts that link to the blog and expand the search timeline - espeically ones that have mutiple tweets already
    
    pass
    
def getOldTweets():
    # get oldest timestamp on tweet
    try:
        driver = webdriver.Chrome()
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

getOldTweets()
