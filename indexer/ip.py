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




THREADS_NUMBER = 3
BATCH_SIZE     = 96 # Number of transactions in one batch

def print_hash(txs):
    for t in txs:
        print(t.hash)

min_height = Transaction.select(fn.MIN(Transaction.height))\
                    .where((Transaction.msg_type == 'claim') & Transaction.servicer_url.is_null()).execute()[0].min

print(f"Min heght: {min_height} - {min_height+BATCH_SIZE}")

count = fn.COUNT(Transaction.signer)
addresses_to_process = Transaction.select(Transaction.signer, count.alias('count'))\
                                    .where((Transaction.msg_type == 'claim') & Transaction.servicer_url.is_null() \
                                                & (Transaction.height >= min_height) & (Transaction.height < (min_height+BATCH_SIZE)))\
                                    .group_by(Transaction.signer)\
                                    .order_by(count.desc())\
                                    .limit(THREADS_NUMBER)

for a in addresses_to_process:
    print(a.signer)
exit()

for i in range(THREADS_NUMBER):
    print(i,len(txs_to_process[i*BATCH_SIZE:(i+1)*BATCH_SIZE]))
    print_hash(txs_to_process[i*BATCH_SIZE:(i+1)*BATCH_SIZE])
    if len(txs_to_process[i*BATCH_SIZE:(i+1)*BATCH_SIZE]) == 0:
        print("Finished")
        break

exit()
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
host = 'e2s001918-pocket-16.easy2stake.com'
ip = dns.resolver.resolve(host, 'A')[0].to_text()
print(ip)
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

