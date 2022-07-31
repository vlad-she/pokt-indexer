# from pokt import PoktRPCDataProvider
from utils import *
from dateutil.parser import parse
from models import *
from threading import Thread
from tqdm import tqdm
import sys
import signal
import threading
import time
import random
import os
# import requests
import json
import datetime
import logging
import dns.resolver
from urllib.parse import urlparse
import argparse
##################

parser = argparse.ArgumentParser(description='The script syncs POKT blocks and txs')
parser.add_argument('-w','--workers', help='Number of workers to sync in parallel', default=1)
args = parser.parse_args()


THREADS_NUMBER = int(args.workers)
WINDOW_SIZE     = 5*96 # Number of blocks to update geo data at once

quit_event = threading.Event()
signal.signal(signal.SIGTERM, lambda *_args: quit_event.set())

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO)

def update_geodata_for_address(from_height: int, to_height: int, address: str):

    mid_height = int((from_height+to_height)/2)
    node = get_node_info(mid_height, address)
    host = urlparse(node['service_url']).hostname
    try:
        # DNS to IP
        ip = dns.resolver.resolve(host, 'A')[0].to_text()
        #IP geolocation
        geo_info = get_ip_geodata(ip=ip)

    except (dns.resolver.NXDOMAIN, dns.resolver.LifetimeTimeout, dns.resolver.NoAnswer):
        logging.warning(f"Couldnot resolve {host} ...")
        geo_info = dict()
        geo_info['city'] = ''
        geo_info['region'] = ''
        geo_info['country'] = ''
        geo_info['latitude'] = ''
        geo_info['longitude'] = ''
        geo_info['org'] = ''
        geo_info['isp'] = ''

    txs_to_update = Transaction.select().where((Transaction.msg_type == 'claim') & Transaction.servicer_url.is_null() \
                                                & (from_height <= Transaction.height) & (Transaction.height <= to_height) \
                                                & (Transaction.signer == address))

    for t in txs_to_update:
        t.servicer_url = host[:60]
        t.city = geo_info['city']
        t.region = geo_info['region']
        t.country = geo_info['country']
        t.latitude = geo_info['latitude']
        t.longitude = geo_info['longitude']
        t.org = geo_info['org']
        t.isp = geo_info['isp']

    Transaction.bulk_update(txs_to_update, fields=[Transaction.servicer_url,
                                            Transaction.city,
                                            Transaction.region,
                                            Transaction.country,
                                            Transaction.latitude,
                                            Transaction.longitude,
                                            Transaction.org,
                                            Transaction.isp
                                            ])

    logging.info(f"{len(list(txs_to_update))} - transactions updated.")
    return True

def main():

    num = 20

    while True:
        if quit_event.is_set():
            logging.info("Safely shutting down")
            quit()

        try:
            print("Update list of txs")
            from_height = Transaction.select(fn.MIN(Transaction.height))\
                                .where((Transaction.msg_type == 'claim') & Transaction.servicer_url.is_null()).execute()[0].min
            to_height = from_height+WINDOW_SIZE

            count = fn.COUNT(Transaction.signer)
            min_height = fn.MIN(Transaction.height)
            addresses_to_process = Transaction.select(min_height.alias('min_height'), Transaction.signer, count.alias('count'))\
                                                .where((Transaction.msg_type == 'claim') & Transaction.servicer_url.is_null() \
                                                            & (Transaction.height >= from_height) & (Transaction.height <= to_height))\
                                                .group_by(Transaction.signer)\
                                                .order_by(min_height.asc(), count.desc())\
                                                .limit(num*THREADS_NUMBER)

            if len(list(addresses_to_process)) == 0:
                break

            threads = []

            for i in range(num):
                with db.atomic() as transaction:  # Opens new transaction.

                    for r in addresses_to_process[i*THREADS_NUMBER:(i+1)*THREADS_NUMBER]:
                        logging.info(f"Updating geo info for signer: {r.signer} withing blocks: {from_height} - {to_height}, oldest height: {r.min_height}")
                        x = Request(target=update_geodata_for_address, args=(from_height, to_height, r.signer))
                        x.start()
                        threads.append(x)

                    for thread in threads:
                        if thread.join() == False:
                            logging.error("Thread failed, quitting")
                            transaction.rollback()
                            quit()

                    transaction.commit()

        except:
            logging.error("Thread failed, quitting", exc_info=True)
            transaction.rollback()
            quit()


if __name__ == "__main__":
    main()
