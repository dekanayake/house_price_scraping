import requests
from lxml.html import fromstring
from lxml import etree
from itertools import cycle
import traceback
import random
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem, Popularity,SoftwareType,HardwareType
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
import sys
import os
import time
import re
from io import StringIO, BytesIO
import pandas as pd, numpy as np
import traceback
import codecs
import logging
from datetime import datetime
from tinydb import TinyDB, Query


logging.basicConfig(
    filename='crawling.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logging.info('Crawling started')
software_names_windows = [SoftwareName.CHROME.value,SoftwareName.FIREFOX.value,SoftwareName.EDGE.value,SoftwareName.OPERA.value]
operating_systems_windows = [OperatingSystem.WINDOWS.value,OperatingSystem.WINDOWS_MOBILE.value,OperatingSystem.WINDOWS_PHONE.value] 

software_names_linux = [SoftwareName.CHROME.value,SoftwareName.FIREFOX.value,SoftwareName.OPERA.value]
operating_systems_linux = [OperatingSystem.LINUX.value,OperatingSystem.ANDROID.value] 

software_names_apple = [SoftwareName.CHROME.value,SoftwareName.FIREFOX.value,SoftwareName.EDGE.value,SoftwareName.OPERA.value,SoftwareName.SAFARI.value]
operating_systems_apple = [OperatingSystem.MAC.value,OperatingSystem.MAC_OS_X.value,OperatingSystem.MACOS.value,OperatingSystem.IOS.value] 

popularity = [Popularity.COMMON.value]
software_types = [SoftwareType.WEB_BROWSER.value]
hardware_types = [HardwareType.COMPUTER.value,HardwareType.MOBILE.value,HardwareType.MOBILE__PHONE.value,HardwareType.MOBILE__TABLET.value]

user_agent_rotator_apple = UserAgent(software_names=software_names_apple, operating_systems=operating_systems_apple,popularity=popularity,software_types=software_types,hardware_types=hardware_types, limit=100)
user_agent_rotator_windows = UserAgent(software_names=software_names_windows, operating_systems=operating_systems_windows,popularity=popularity,software_types=software_types,hardware_types=hardware_types, limit=100)
user_agent_rotator_linux = UserAgent(software_names=software_names_linux, operating_systems=operating_systems_linux,popularity=popularity,software_types=software_types,hardware_types=hardware_types, limit=100)

proxy = "socks5://dumindae%40gmail.com:Hiru%40Vertx88@ie.socks.nordhold.net:1080"
http_proxy = "http://dumindae%40gmail.com:Hiru%40Vertx88@ie.socks.nordhold.net:1080"

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver.exe")

street_name_abrv_map = {
    "avenue":"ave",
    "boulevard":"blvd",
    "building":"bldg",
    "court":"ct",
    "crescent":"cres",
    "drive":"dr",
    "place":"pl",
    "road":"rd",
    "square":"sq",
    "station":"stn",
    "street":"st",
    "terrace":"terr",
    "close":"cl",
    "grove":"gr",
    "circuit":"cct",
}

month = {
  'January':1,
  'February':2,
  'March':3,
  'April':4,
  'May':5,
  'June':6,
  'July':7,
  'August':8,
  'September':9,
  'October':10,
  'November':11,
  'December':12,
}

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:100]:
        if i.xpath('.//td[7][contains(text(),"yes")]') and i.xpath('.//td[5][contains(text(),"elite proxy")]') and i.xpath('.//td[8][contains(text(),"1 minute ago")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

def get_proxy():
    proxies = get_proxies()
    proxy_pool = cycle(proxies)
    proxy = next(proxy_pool)
    print(proxy)
    return proxy

def get_user_agent():
    user_agent_list = [
      user_agent_rotator_apple.get_random_user_agent(),
      user_agent_rotator_windows.get_random_user_agent(),
      user_agent_rotator_linux.get_random_user_agent()
    ]
    user_agent  = random.choice(user_agent_list)
    return user_agent


def get_streets(url,user_agent,proxy):
    response = requests.get(url,headers={
        'User-Agent': get_user_agent(),
    })
    parser = fromstring(response.text)
    streets = {}
    logging.info("------------Extracting streets------------")
    for street in parser.xpath('//ul/li/a/text()'):
      logging.info(re.sub('\s+',' ',street))
      street_name = re.sub('\s+',' ',street).lower().replace(' ', '-')
      for key, value in street_name_abrv_map.items():
        street_name = street_name.replace("-" + key, "-" + value)
      streets[street_name] = re.sub('\s+',' ',street)
    return streets


def get_properties_in_street(url,user_agent,proxy):
    response = requests.get(url,headers={
        'User-Agent': get_user_agent(),
    })
    parser = fromstring(response.text)
    properties = set()
    for i in parser.xpath('//a[contains(@class, "property-card-link")]/@href'):
      properties.add(i)
    return properties


def  get_sale_listing_details(url,user_agent,proxy):
    user_agent = get_user_agent()
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    # options.add_argument("--proxy-server" + proxy);
    options.add_argument('--always-authorize-plugins=true')
    options.add_argument("--incognito")
    options.add_argument("user-agent=" + user_agent)
    options.add_argument("--disable-blink-features");
    options.add_argument("--disable-blink-features=AutomationControlled"); 

    wd = webdriver.Chrome(options=options,executable_path=DRIVER_BIN)
    wd.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
    wd.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
      "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
    })
    wd.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    wd.get(url)
    time.sleep(15)

    listing_details = {}
    parser = fromstring(wd.page_source)
    property_type = parser.xpath('//span[@class="property-info__property-type"]/text()')[0]
    listing_details['property_type'] = property_type
    listed_price = parser.xpath('//span[@class="property-price property-info__price"]/text()')[0] if (len(parser.xpath('//span[@class="property-price property-info__price"]/text()')) > 0) else ''
    listed_price = re.sub('\s+',' ',listed_price)
    if listed_price:
      listed_price_arr = listed_price.split('-')
      if len(listed_price_arr) == 2:
        fromPrice = float(re.sub('[\$,]', '',listed_price_arr[0]))
        listing_details['from_price'] = fromPrice
        toPrice = float(re.sub('[\$,]', '',listed_price_arr[1]))
        listing_details['to_price'] = toPrice
      else:
        price = float(re.sub('[\$,]', '',listed_price_arr[0]))
        listing_details['from_price'] = price
        listing_details['to_price'] = price
    listing_details['url'] = url

    wd.quit()
    return listing_details
      



def get_property_details(url,proxy):
    user_agent = get_user_agent()
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    # options.add_argument("--proxy-server" + proxy);
    options.add_argument('--always-authorize-plugins=true')
    options.add_argument("--incognito")
    options.add_argument("user-agent=" + user_agent)
    options.add_argument("--disable-blink-features");
    options.add_argument("--disable-blink-features=AutomationControlled");  
    

    wd = webdriver.Chrome(options=options,executable_path=DRIVER_BIN)
    
    wd.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
    wd.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
      "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
    })
    wd.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    wd.get(url)
    time.sleep(15)

    parser = fromstring(wd.page_source)
    short_address= parser.xpath('//div[@class="property-info__short-address"]/text()')[0]
    suburb = parser.xpath('//span[@itemprop="addressLocality"]/text()')[0]
    state = parser.xpath('//span[@itemprop="addressRegion"]/text()')[0]
    postCode = parser.xpath('//span[@itemprop="postalCode"]/text()')[0]

    bedroomsElement = parser.xpath('//span[@class="rui-property-feature"]/span/span[text()="Bedrooms"]/../..')[0]
    bedroom  = etree.parse(StringIO(etree.tostring(bedroomsElement).decode("utf-8")), etree.HTMLParser()).xpath('//span[@class="config-num"]/text()')[0]
    bedroom = re.sub('\s+',' ',bedroom) 
    bedroom = int(bedroom) if bedroom != '-' else 0

    bathroomsElement = parser.xpath('//span[@class="rui-property-feature"]/span/span[text()="Bathrooms"]/../..')[0]
    bathroom  = etree.parse(StringIO(etree.tostring(bathroomsElement).decode("utf-8")), etree.HTMLParser()).xpath('//span[@class="config-num"]/text()')[0]
    bathroom = re.sub('\s+',' ',bathroom) 
    bathroom = int(bathroom) if bathroom != '-' else 0

    carSpacesElement = parser.xpath('//span[@class="rui-property-feature"]/span/span[text()="Car Spaces"]/../..')[0]
    carSpaces  = etree.parse(StringIO(etree.tostring(carSpacesElement).decode("utf-8")), etree.HTMLParser()).xpath('//span[@class="config-num"]/text()')[0]
    carSpaces = re.sub('\s+',' ',carSpaces) 
    carSpaces = int(carSpaces) if carSpaces != '-' else 0

    landSizeString = re.sub('\s+',' ',parser.xpath('//table[@class="info-table"]/tbody/tr[position()=1]/td[position()=2]/text()')[0])
    landSizeString = re.sub(',+','',landSizeString) if landSizeString != 'Unavailable'  else '0.0'
    landSizeStrings = landSizeString.split()
    landSize = float(landSizeStrings[0]) if (len(landSizeStrings) > 0) else 0.0
    landSizeMeasurement = landSizeStrings[1] if (len(landSizeStrings) > 1) else ''
    floorArea = parser.xpath('//table[@class="info-table"]/tbody/tr[position()=2]/td[position()=2]/text()')[0]
    yearBuilt = parser.xpath('//table[@class="info-table"]/tbody/tr[position()=3]/td[position()=2]/text()')[0]

    forSale = True if parser.xpath('//span[@class="property-status-text"]/text()')[0] == 'FOR SALE' else False
    
    listing_details = {
      'property_type':'',
      'from_price':0.0,
      'to_price':0.0,
      'url':''
    }
    if forSale:
      listing_url = parser.xpath('//div[@class="property-info__market-status"]/a/@href')[0]
      listing_details = get_sale_listing_details(listing_url,get_user_agent(),proxy)


    timelines = parser.xpath('//ul[@class="property-timeline__container with_all"]/li')
    data_set = []
    if timelines:
     for timeline in timelines:
      timeLineParser = etree.parse(StringIO(etree.tostring(timeline).decode("utf-8")))
      soldTime = re.sub('\s+',' ',timeLineParser.xpath('//span[@class="property-timeline__date"]/text()')[0])
      soldMonth = month[soldTime.split()[0]]
      soldYear = int(soldTime.split()[1])
      soldPriceString = timeLineParser.xpath('//div[@class="property-timeline__price"]/text()')[0] if (len(timeLineParser.xpath('//div[@class="property-timeline__price"]/text()')) > 0) else 'NO_PRICE'
      soldPriceString = re.sub('\s+',' ',soldPriceString)
      soldPrice = 0.0 if soldPriceString == 'NO_PRICE' else float(re.sub('[\$,]', '',soldPriceString))
      data = [
        re.sub('\s+',' ',short_address), 
        re.sub('\s+',' ',suburb), 
        re.sub('\s+',' ',postCode), 
        re.sub('\s+',' ',state), 
        bedroom, 
        bathroom, 
        carSpaces,
        landSize,
        landSizeMeasurement,
        '"' + re.sub('\s+',' ',floorArea) + '"',
        re.sub('\s+',' ',yearBuilt),
        soldMonth,
        soldYear,
        soldPrice,
        forSale,
        listing_details['property_type'],
        listing_details['from_price'],
        listing_details['to_price'],
        listing_details['url']
        ]
      data_set.append(data)
    else:
      logging.info("No transaction history for :" + url)
      data = [
        re.sub('\s+',' ',short_address), 
        re.sub('\s+',' ',suburb), 
        re.sub('\s+',' ',postCode), 
        re.sub('\s+',' ',state), 
        bedroom, 
        bathroom, 
        carSpaces,
        landSize,
        landSizeMeasurement,
        '"' + re.sub('\s+',' ',floorArea) + '"',
        re.sub('\s+',' ',yearBuilt),
        0,
        0,
        0.0,
        forSale,
        listing_details['property_type'],
        listing_details['from_price'],
        listing_details['to_price'],
        listing_details['url']
        ]
      data_set.append(data)

    wd.quit()
    return data_set




def scrapeForSuburb(streetsUrl,realEstateSuburubBaseUrl,outFileName):
  try:  
      # response = requests.get(url,proxies={"http": proxy, "https": proxy},headers=headers)
      # print(response.json())
      outfile = outFileName
      count = 1
      with codecs.open(outfile, 'w','utf-8') as csvfile:
        header = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (
          'Short Address',
          'Suburub', 
          'PostCode', 
          'State', 
          'Bedroom',
          'Bathroom', 
          'Car spaces',
          'Land size',
          'Land size Measurment',
          'Floor area',
          'Year built',
          'Sold year',
          'Sold month',
          'Sold  price',
          'URL',
          'For Sale',
          'For Sale Property Type',
          'Sale From Price',
          'Sale To Price',
          'Sale Url')
        csvfile.write(header)
        for  street_url_path,street_name in get_streets(streetsUrl,get_user_agent(),proxy).items():
          street_url = realEstateSuburubBaseUrl + street_url_path
          logging.info('processing street :' + street_name)
          properties = get_properties_in_street(street_url,get_user_agent(),proxy)
          if not  properties:
            logging.info("No porperties for :" + street_url + " street name " + street_name)
          for property_url in properties:
            try:
              property_data_set = get_property_details(property_url,proxy)
              for property_data in property_data_set:
                data = '%s,%s,%s,%s,%i,%i,%i,%f,%s,%s,%s,%i,%i,%f,%s,%r,%s,%f,%f,%s,\n' % (
                  property_data[0],
                  property_data[1],
                  property_data[2],
                  property_data[3],
                  property_data[4],
                  property_data[5],
                  property_data[6],
                  property_data[7],
                  property_data[8],
                  property_data[9],
                  property_data[10],
                  property_data[11],
                  property_data[12],
                  property_data[13],
                  property_url,
                  property_data[14],
                  property_data[15],
                  property_data[16],
                  property_data[17],
                  property_data[18],
                  )
                csvfile.write(data)
                count+=1
                if count == 100:
                  csvfile.flush()
                  count = 0
            except Exception as e:
              logging.error("Error occured property url : " + property_url)
              logging.error(e, exc_info=True)
  except Exception as e:
      logging.error("Error occured")
      traceback.print_exc() 
      logging.error(e, exc_info=True)
      #Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work. 
      #We will just skip retries as its beyond the scope of this tutorial and we are only downloading a single url 


def scrapeStreetUrls(street_urls,  outFileName):
  logging.info('Scraping properties from street urls')
  try:
      outfile = outFileName
      count = 1
      with codecs.open(outfile, 'a','utf-8') as csvfile:
        for  street_url in street_urls:
          logging.info('processing street url :' + street_url)
          properties = get_properties_in_street(street_url,get_user_agent(),proxy)
          if not  properties:
            logging.info("No porperties for :" + street_url )
          for property_url in properties:
            try:
              property_data_set = get_property_details(property_url,proxy)
              for property_data in property_data_set:
                data = '%s,%s,%s,%s,%i,%i,%i,%f,%s,%s,%s,%i,%i,%f,%s,%r,%s,%f,%f,%s,\n' % (
                    property_data[0],
                    property_data[1],
                    property_data[2],
                    property_data[3],
                    property_data[4],
                    property_data[5],
                    property_data[6],
                    property_data[7],
                    property_data[8],
                    property_data[9],
                    property_data[10],
                    property_data[11],
                    property_data[12],
                    property_data[13],
                    property_url,
                    property_data[14],
                    property_data[15],
                    property_data[16],
                    property_data[17],
                    property_data[18],
                    )
                csvfile.write(data)
                count+=1
                if count == 100:
                  csvfile.flush()
                  count = 0
            except Exception as e:
              logging.error("Error occured property url : " + property_url)
              logging.error(e, exc_info=True)
  except Exception as e: 
    logging.error("Error occured") 
    logging.error(e, exc_info=True)


def scrapePropertyUrls(property_urls,  outFileName):
  logging.info('Scraping properties from urls')
  try:
      outfile = outFileName
      count = 1
      with codecs.open(outfile, 'a','utf-8') as csvfile:
        for  property_url in property_urls:
          logging.info('processing property url :' + property_url)
          try:
            property_data_set = get_property_details(property_url,proxy)
            for property_data in property_data_set:
              data = '%s,%s,%s,%s,%i,%i,%i,%f,%s,%s,%s,%i,%i,%f,%s,%r,%s,%f,%f,%s,\n' % (
                    property_data[0],
                    property_data[1],
                    property_data[2],
                    property_data[3],
                    property_data[4],
                    property_data[5],
                    property_data[6],
                    property_data[7],
                    property_data[8],
                    property_data[9],
                    property_data[10],
                    property_data[11],
                    property_data[12],
                    property_data[13],
                    property_url,
                    property_data[14],
                    property_data[15],
                    property_data[16],
                    property_data[17],
                    property_data[18],
                    )
              csvfile.write(data)
              count+=1
              if count == 100:
                csvfile.flush()
                count = 0
          except Exception as e:
            logging.error("Error occured property url : " + property_url)
            logging.error(e, exc_info=True)
  except Exception as e: 
    logging.error("Error occured") 
    logging.error(e, exc_info=True)

# scrapeForSuburb("https://geographic.org/streetview/australia/vic/croydon_south.html","https://www.realestate.com.au/vic/croydon-south-3136/","croydon_south_houses.csv")

# scrapeStreetUrls([
#   "https://www.realestate.com.au/vic/croydon-south-3136/azarow-cct",
#   "https://www.realestate.com.au/vic/croydon-south-3136/belmont-rd-e",
#   "https://www.realestate.com.au/vic/croydon-south-3136/belmont-rd-w",
#   "https://www.realestate.com.au/vic/croydon-south-3136/blazey-rd",
#   "https://www.realestate.com.au/vic/croydon-south-3136/the-common",
#   "https://www.realestate.com.au/vic/croydon-south-3136/the-mount",
#   "https://www.realestate.com.au/vic/croydon-south-3136/the-place"
# ],"croydon_south_houses.csv")

scrapePropertyUrls([
  "https://www.realestate.com.au/property/6-mulduri-cres-croydon-south-vic-3136"
],"croydon_south_houses.csv")