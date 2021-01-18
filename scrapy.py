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

proxy = "socks5://1080"
http_proxy = "http://1080"

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")

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



def get_properties_in_street(url,user_agent,proxy):
    response = requests.get(url,proxies={"http": proxy, "https": proxy},headers={
        'User-Agent': get_user_agent(),
    })
    parser = fromstring(response.text)
    properties = set()
    for i in parser.xpath('//a[contains(@class, "property-card-link")]/@href'):
      properties.add(i)
    return properties

def get_property_details(url,user_agent,proxy,final_data):
    print(user_agent)
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
    time.sleep(10)

    parser = fromstring(wd.page_source)
    short_address= parser.xpath('//div[@class="property-info__short-address"]/text()')[0]
    suburb = parser.xpath('//span[@itemprop="addressLocality"]/text()')[0]
    state = parser.xpath('//span[@itemprop="addressRegion"]/text()')[0]
    postCode = parser.xpath('//span[@itemprop="postalCode"]/text()')[0]

    bedroomsElement = parser.xpath('//span[@class="rui-property-feature"]/span/span[text()="Bedrooms"]/../..')[0]
    bedroom  = etree.parse(StringIO(etree.tostring(bedroomsElement).decode("utf-8")), etree.HTMLParser()).xpath('//span[@class="config-num"]/text()')[0]

    bathroomsElement = parser.xpath('//span[@class="rui-property-feature"]/span/span[text()="Bathrooms"]/../..')[0]
    bathroom  = etree.parse(StringIO(etree.tostring(bathroomsElement).decode("utf-8")), etree.HTMLParser()).xpath('//span[@class="config-num"]/text()')[0]

    carSpacesElement = parser.xpath('//span[@class="rui-property-feature"]/span/span[text()="Car Spaces"]/../..')[0]
    carSpaces  = etree.parse(StringIO(etree.tostring(carSpacesElement).decode("utf-8")), etree.HTMLParser()).xpath('//span[@class="config-num"]/text()')[0]

    landSize = parser.xpath('//table[@class="info-table"]/tbody/tr[position()=1]/td[position()=2]/text()')[0]
    floorArea = parser.xpath('//table[@class="info-table"]/tbody/tr[position()=2]/td[position()=2]/text()')[0]
    yearBuilt = parser.xpath('//table[@class="info-table"]/tbody/tr[position()=3]/td[position()=2]/text()')[0]

    timelines = parser.xpath('//ul[@class="property-timeline__container with_all"]/li')
    if timelines:
     for timeline in timelines:
      timeLineParser = etree.parse(StringIO(etree.tostring(timeline).decode("utf-8")))
      soldTime = timeLineParser.xpath('//span[@class="property-timeline__date"]/text()')[0]
      soldPrice = timeLineParser.xpath('//div[@class="property-timeline__price"]/text()')[0]
      data = [re.sub('\s+',' ',short_address), re.sub('\s+',' ',suburb), re.sub('\s+',' ',postCode), re.sub('\s+',' ',state), re.sub('\s+',' ',bedroom), re.sub('\s+',' ',bathroom), re.sub('\s+',' ',carSpaces),re.sub('\s+',' ',landSize),re.sub('\s+',' ',floorArea),re.sub('\s+',' ',yearBuilt),re.sub('\s+',' ',soldTime),re.sub('\s+',' ',soldPrice)]
      final_data.append(data)
    else:
      data = [re.sub('\s+',' ',short_address), re.sub('\s+',' ',suburb), re.sub('\s+',' ',postCode), re.sub('\s+',' ',state), re.sub('\s+',' ',bedroom), re.sub('\s+',' ',bathroom), re.sub('\s+',' ',carSpaces),re.sub('\s+',' ',landSize),re.sub('\s+',' ',floorArea),re.sub('\s+',' ',yearBuilt),'','']
      final_data.append(data)



    wd.quit()


try:  
    # response = requests.get(url,proxies={"http": proxy, "https": proxy},headers=headers)
    # print(response.json())
    properties = get_properties_in_street('https://www.realestate.com.au/vic/ringwood-east-3135/hilary-gr/',get_user_agent(),proxy)
    final_data = []
    for property in properties:
      get_property_details(property,get_user_agent(),proxy,final_data)
    
    labels = ['Short Address','Suburub', 'PostCode', 'State', 'Bedroom','Bathroom', 'Car spaces','Land size','Floor area','Year built','Sold time','Sold  price']
    export_dataframe_1_medium = pd.DataFrame.from_records(final_data, columns=labels)
    export_dataframe_1_medium.to_csv('export_dataframe_2_medium.csv')
except Exception as e:
    print("Skipping. Connnection error")
    print(e)
    #Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work. 
    #We will just skip retries as its beyond the scope of this tutorial and we are only downloading a single url 