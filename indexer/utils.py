from ipaddress import ip_address
from pokt import PoktRPCDataProvider
from threading import Thread
import json
import requests
import datetime
import os
import time
import random
import logging
from urllib.parse import urlparse
import dns.resolver
from models import *

POKT_RPC = "https://mainnet.gateway.pokt.network/v1/lb/62afb0c3123e6f003979d144"

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    # handlers=[
                    #     logging.FileHandler("poktwatch.log"),
                    #     logging.StreamHandler()
                    # ],
                    level=logging.INFO)
# allows threading functions to have return values
#Timeout     (Connect, Read)
REQ_TIMEOUT = (5,15)

class Request(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def get_block(
    height: int,
    retries: int = 10
):
    for i in range(retries):
        try:
            resp = requests.post(f"{POKT_RPC}/v1/query/block",
                                    json={"height": height},
                                    timeout=REQ_TIMEOUT)
            if resp.status_code == 200 :
                return resp.json()
            else:
                raise Exception(f"Reply status code: {resp.status_code} != 200")
        except Exception as e:
            logging.warning(f"Failed to get_block, {e}")
            time.sleep(random.randint(3, 7))

    raise Exception("get_block failed")
    quit()

def get_block_transactions(
    height: int,
    page: int,
    per_page: int = 50,
    order: str = "desc",
    # session: Optional[requests.Session] = None,
    retries: int = 10
):
    for i in range(retries):
        try:
            resp = requests.post(f"{POKT_RPC}/v1/query/blocktxs",
                                    json={"height": height, "page": page, "per_page": per_page, "sort": order},
                                    timeout=REQ_TIMEOUT)

            if resp.status_code == 200 :
                return resp.json()
            else:
                raise Exception(f"Reply status_code: {resp.status_code} != 200")
        except Exception as e:
            logging.warning(f"Failed to get_block_transactions, {e}")
            time.sleep(random.randint(3, 7))

    raise Exception(f"get_block_transactions failed, out of retries height: {height}, page: {page}")
    quit()

def get_block_txs(height: int, retries: int = 20, batch: int = 50):
    """ get all transaction of a block ordered by index (native)
    height - the height to query blocktxs for
    retries - the number of times to retry if there is an RPC error
    per_page - the per_page query of the RPC request, smaller for thinner machines
    pokt_rpc - the PoktRPCDataProvider object to query
    """
    page = 1
    txs = []
    while retries > 0:
        try:
            block_txs = get_block_transactions(height=height, page=page, per_page=batch)

            if (block_txs['txs'] == []):
                return txs
            else:
                txs.extend(block_txs['txs'])
                page += 1

        except Exception as e:
            logging.warning(f"Failed to get_block_txs height: {height}, {e}")
            retries -= 1
            if retries < 0:
                raise Exception(f"Out of retries getting block {height} transactions page {page}")
            time.sleep(random.randint(3, 7))


    raise Exception("get_block_txs failed.")
    quit()

def flatten_tx(tx, RelaysToTokensMultiplier: int, timestamp):
    """ flatten a tx to the json requirements according to models.py

    tx - the Transaction to flatten
    RelaysToTokensMultiplier - the RelaysToTokensMultiplier at that current block, this is used for calculating the value of a claim
    timestamp - the block timestamp of the height of the tx

    """

    session_block_height = None
    servicer_pub_key = ''
    amount = 0
    app_pub_key = ''
    chain = ''
    total_proofs = None
    message_type = tx['tx_result']['message_type']

    if message_type == "send":
        amount       = tx['stdTx']['msg']['value']['amount']

    elif message_type == "claim":
        app_pub_key = tx['stdTx']['msg']['value']['header']['app_public_key'] # -> App_address
        chain = tx['stdTx']['msg']['value']['header']['chain']
        session_block_height = tx['stdTx']['msg']['value']['header']['session_height']
        total_proofs = int( tx['stdTx']['msg']['value']['total_proofs'])
        amount = total_proofs * RelaysToTokensMultiplier

    elif message_type == "proof":
        app_pub_key = tx['stdTx']['msg']['value']['leaf']['value']['aat']['app_pub_key'] # -> App_address
        chain = tx['stdTx']['msg']['value']['leaf']['value']['blockchain']
        servicer_pub_key = tx['stdTx']['msg']['value']['leaf']['value']['servicer_pub_key'] # NODE's pub key
        session_block_height = tx['stdTx']['msg']['value']['leaf']['value']['session_block_height']

    elif message_type == "stake_validator":
        amount       = tx['stdTx']['msg']['value']['value']
        servicer_pub_key = tx['stdTx']['msg']['value']['public_key']['value'] # NODE's pub key

    elif message_type in ["unjail_validator", "begin_unstake_validator"]:
        servicer_pub_key = tx['stdTx']['signature']['pub_key'] # NODE's pub key

    else:
        print(f"Not known message_type: {message_type} hash: {tx['hash']}")

    # few edge cases with 0 fee transaction
    if len(tx['stdTx']['fee']) == 0:
        fee = 0
    else:
        fee = tx['stdTx']['fee'][0]['amount']

    return {
        "height": tx['height'],
        "hash": tx['hash'],
        "index": tx['index'],
        "result_code": tx['tx_result']['code'],
        "app_pub_key": app_pub_key,
        "chain": chain,
        "servicer_pub_key": servicer_pub_key,
        "signer": tx['tx_result']['signer'],
        "recipient": tx['tx_result']['recipient'],
        "msg_type": message_type,
        "total_proofs": total_proofs,
        "fee": fee,
        "memo": tx['stdTx']['memo'],
        "amount": amount,
        "timestamp": timestamp
    }

def get_ip_geodata(
    ip: str,
    retries: int = 10
):
    # GEO_API = f"http://ipwho.is/{ip}"
    GEO_API = f"http://ipwhois.pro/{ip}?key=F4FxHG84LLM1uZ2F"
    # GEO_API = f"https://ipapi.co/{ip}/json/"
    GEO_DATA_TTL = 7*86400 # 3*24 hours

    try:
        geoinfo = GeoCache.get(GeoCache.ip_address == ip)
        if int(time.time())-geoinfo.timestamp < GEO_DATA_TTL:
            return {
                "city" : geoinfo.city,
                "region" : geoinfo.region,
                "country" : geoinfo.country,
                "latitude" : geoinfo.latitude,
                "longitude" : geoinfo.longitude,
                "org" : geoinfo.org,
                "isp" : geoinfo.isp
            }
        else:
            GeoCache.delete().where(GeoCache.ip_address == ip).execute()
            raise Exception(f"Updating cached info for ip: {ip}")

    except Exception as e:
        # print("No CACHE for the ip", e)
        for i in range(retries):
            try:
                resp = requests.get(GEO_API, timeout=REQ_TIMEOUT)

                if resp.status_code == 200 :
                    geo_json = json.loads(resp.text)
                    GeoCache.insert(
                        ip_address=ip,
                        timestamp=int(time.time()),
                        city=geo_json['city'][:60],
                        region=geo_json['region'][:60],
                        country=geo_json['country'][:60],
                        latitude=str(geo_json['latitude'])[:15],
                        longitude=str(geo_json['longitude'])[:15],
                        org=geo_json['connection']['org'][:60],
                        isp=geo_json['connection']['isp'][:60]
                    ).execute()

                    return {
                        "city" : geo_json['city'][:60],
                        "region" : geo_json['region'][:60],
                        "country" : geo_json['country'][:60],
                        "latitude" : str(geo_json['latitude'])[:15],
                        "longitude" : str(geo_json['longitude'])[:15],
                        "org" : geo_json['connection']['org'][:60],
                        "isp" : geo_json['connection']['isp'][:60]
                    }

                else:
                    raise Exception(f"get_ip_geolocation Reply status_code: {resp.status_code} != 200")
            except Exception as e:
                logging.warning(f"Failed to get_ip_geolocation, {e}")
                time.sleep(random.randint(3, 7))

    raise Exception(f"get_ip_geolocation failed, out of retries ip: {ip}, API: {GEO_API}")
    quit()


def get_node_info(
    height: int,
    address: str,
    retries: int = 10
):
    for i in range(retries):
        try:
            resp = requests.post(f"{POKT_RPC}/v1/query/node",
                                    json={"height": height, "address": address},
                                    timeout=REQ_TIMEOUT)

            if resp.status_code == 200 :
                return resp.json()
            else:
                raise Exception(f"Reply status_code: {resp.status_code} != 200")
        except Exception as e:
            logging.warning(f"Failed to get_node_info, {e}")
            time.sleep(random.randint(3, 7))

    raise Exception(f"get_node_info failed, out of retries height: {height}, address: {address}")
    quit()


# def flatten_pending_tx(raw_tx: str, RelaysToTokensMultiplier: int):
#     """ flatten a raw tx string to the json requirements according to models.py

#     raw_tx - the raw transaction string to flatten
#     RelaysToTokensMultiplier - the RelaysToTokensMultiplier at that current block, this is used for calculating the value of a claim

#     """

#     res = os.popen('pocket util decode-tx {} false true'.format(raw_tx)).read()

#     try:
#         tx = json.loads(res, strict=False)

#         if tx["type"] == "send":
#             amount = tx["msg"]["amount"]
#         elif tx["type"] == "claim":
#             amount = tx["msg"]["total_proofs"] * RelaysToTokensMultiplier
#         else:
#             amount = 0

#         return {
#             "height": -1,
#             "hash": tx["hash"].upper(),
#             "index": -1,
#             "result_code": -1,
#             "signer": tx["signer"].upper(),
#             "recipient": tx["receiver"].upper(),
#             "msg_type": tx["type"],
#             "fee": int(tx["fee"][:5]),
#             "memo": tx["memo"],
#             "amount": amount,
#             "timestamp": datetime.datetime.now()
#         }
#     except Exception as e:
#         logging.error("Raw_tx decoding error {}. Tx result {}".format(e, res))

#         quit()
