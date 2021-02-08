import pandas as pd, numpy as np
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem, Popularity,SoftwareType,HardwareType
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
import time
import codecs
import logging
from datetime import datetime

def  configLog(suburbName):
  fileNamePrefix = suburbName.lower()
  fileNamePrefix = '-'.join(fileNamePrefix.split())
  dateTimePrefix  =  datetime.now().strftime("%m%d%Y%H%M%S")
  logging.basicConfig(
      filename= fileNamePrefix + "_" +  dateTimePrefix + "_geo_update.log",
      format='%(asctime)s %(levelname)-8s %(message)s',
      level=logging.INFO,
      datefmt='%Y-%m-%d %H:%M:%S')
  logging.info('Geo update started for  ' + suburbName)

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

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver.exe")


def read_geo(url):
    user_agent = get_user_agent()
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    # options.add_argument("--proxy-server" + proxy);
    options.add_argument('--always-authorize-plugins=true')
    options.add_argument("--incognito")
    options.add_argument("user-agent=" + user_agent)
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled"); 

    wd = webdriver.Chrome(options=options,executable_path=DRIVER_BIN)
    wd.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
    wd.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
      "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
    })
    wd.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    wd.get(url)
    time.sleep(15)

    lon =  wd.execute_script('return REA.lon')
    lat = wd.execute_script('return REA.lat')
    wd.quit()

    return lon,lat


def get_user_agent():
    user_agent_list = [
      user_agent_rotator_apple.get_random_user_agent(),
      user_agent_rotator_windows.get_random_user_agent(),
      user_agent_rotator_linux.get_random_user_agent()
    ]
    user_agent  = random.choice(user_agent_list)
    return user_agent

labels = [
    'Short Address',
    'Suburub',
    'PostCode',
    'State',
    'Property type',
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
    'Sale Url',
    'Lat',
    'Lon']

def update_geo(dataInFileName,dataOutFileName):
    try:
        number_lines = sum(1 for row in (open(dataInFileName)))
        chunksize = 100
        cached_urls = []
        cached_coords = {}
        with codecs.open(dataOutFileName, 'w','utf-8') as csvfile:
            header = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (
                'Short Address',
                'Suburub', 
                'PostCode', 
                'State',
                'Property type', 
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
                'Sale Url',
                'Lon',
                'Lat')
            csvfile.write(header)

            for i in range(1,number_lines,chunksize):
                df = pd.read_csv(dataInFileName,
                    header=None,
                    nrows = chunksize,#number of rows to read at each loop
                    skiprows = i)#skip rows that have been read

                property_list = df.values.tolist()
                property_out_list = []
                for property in property_list:
                    try:
                        url = property[15]
                        if url in cached_coords:
                            lon = cached_coords[url]['Lon']
                            lat = cached_coords[url]['Lat']
                        else:    
                            lon, lat  = read_geo(url)
                            cached_urls.append(url)
                            cached_coords[url] = {
                                'Lon' : lon,
                                'Lat' : lat
                            }
                        property.append(lon)
                        property.append(lat)
                    
                        if len(cached_urls) == 100:
                            cached_url = cached_urls.pop(0)
                            cached_coords.pop(cached_url)
                        property_out_list.append(property)
                    except Exception as e: 
                        logging.error("Error occured property url : " + url)
                        logging.error(e, exc_info=True)


                count = 1
                for property_data in property_out_list:
                    data = '%s,%s,%s,%s,%s,%i,%i,%i,%f,%s,%s,%s,%i,%i,%f,%s,%r,%s,%f,%f,%s,%s,%s\n' % (
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
                    property_data[14],
                    property_data[15],
                    property_data[16],
                    property_data[17],
                    property_data[18],
                    property_data[19],
                    property_data[20],
                    property_data[22],
                    property_data[23]
                    )
                    csvfile.write(data)
                    count+=1
                    if count == 100:
                        csvfile.flush()
                        count = 0
    except Exception as e: 
        logging.error("Error occured") 
        logging.error(e, exc_info=True)






configLog('Croydon South')
update_geo('croydon_south_houses.csv','croydon_south_houses_with_geo.csv')