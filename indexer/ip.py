import dns.resolver
import requests
from urllib.parse import urlparse
import logging
import json

from models import *
from utils import *
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    # handlers=[
                    #     logging.FileHandler("poktwatch.log"),
                    #     logging.StreamHandler()
                    # ],
                    level=logging.INFO)
REQ_TIMEOUT = (10,10)

# def get_ip_geolocation(
#     ip: str,
#     retries: int = 10
# ):
#     GEO_API = f"http://ipwho.is/{ip}"

#     # GEO_API = f"https://ipapi.co/{ip}/json/"
#     for i in range(retries):
#         try:
#             resp = requests.get(GEO_API, timeout=REQ_TIMEOUT)

#             if resp.status_code == 200 :
#                 geo_json = json.loads(resp.text)
#                 print(geo_json)
#                 return {
#                     "city" : geo_json['city'],
#                     "region" : geo_json['region'],
#                     "country" : geo_json['country'],
#                     "latitude" : geo_json['latitude'],
#                     "longitude" : geo_json['longitude'],
#                     "org" : geo_json['connection']['org'],
#                     "isp" : geo_json['connection']['isp']
#                 }

#             else:
#                 raise Exception(f"get_ip_geolocation Reply status_code: {resp.status_code} != 200")
#         except Exception as e:
#             logging.warning(f"Failed to get_ip_geolocation, {e}")
#             time.sleep(random.randint(3, 7))

#     raise Exception(f"get_ip_geolocation failed, out of retries ip: {ip}, API: {GEO_API}")
#     quit()

def rr(dd):
    for i in dd:
        i['new'] = 5

    return dd


t = [{'a': 'b'},{'c':'d'}]
print(t)

r = rr(t)

print(r)
print(t)
exit()
t['r'] = 'ttt'
print(t)
exit()

# print(f"""host: {host}
# ip: {ip}
# geo:{geo_info}""")
ip = '154.53.53.249'

# GeoCache.insert(
#     ip_address="1.1.1.1",
#     timestamp=int(time.time()),
#     city="geo_json['city']",
#     region="geo_json['region']",
#     country="geo_json['country']",
#     isp="geo_json['connection']['isp']"
# ).execute()


geoinfo = GeoCache.get(GeoCache.ip_address == ip)
print(geoinfo.timestamp, geoinfo.city)
p = get_ip_geodata(ip)
print(p)

p = get_ip_geodata('164.90.231.150')
print(p)


node = 'https://val1637640521.c0d3r.org'
host = urlparse(node).hostname
try:
    ip = dns.resolver.resolve(host, 'A')[0].to_text()
except dns.resolver.NXDOMAIN:
    print(f"dns.resolver.NXDOMAIN cannot resolve DNS name")
except Exception as e:
    print(f"Exception in sync_block: {e}")

# geoinfo = GeoCache.get(GeoCache.ip_address == ip)
# try:

#     info = GeoCache.get(GeoCache.ip_address == "1.1.1.1")
#     print(info.ip_address," = ",info.city)
#     print(info)

# except Exception as e:
#     print("Not exist", e)

