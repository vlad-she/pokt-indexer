from pokt import PoktRPCDataProvider
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
##################

""" for syncing early blocks on beefy machines,
there is batching/threading functionality, which is a arg in the entrypoint.sh
file. It is currently set to 1 for stability.
"""
THREADS_NUMBER = 2

POKT_RPC = "https://https://pnfchains:dr8QMogkhDvQSFJaH6b4@pokt-dispatchers.europe-west3.poktnodes.network"
#mainnet.gateway.pokt.network/v1/lb/62afb0c3123e6f003979d144"
# utils.POKT_RPC = POKT_RPC

pokt_rpc = PoktRPCDataProvider(POKT_RPC)

quit_event = threading.Event()
signal.signal(signal.SIGTERM, lambda *_args: quit_event.set())

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO)

# def update_mempool(retries: int):
#     """ get all transactions in the mempool and add them to the database

#     retries - the number of times to allow for a failed request

#     """
#     while retries > 0:
#         try:
#             unconfirmed_txs = requests.get(
#                 "http://pocket:26657/unconfirmed_txs?limit=10000").json()
#             logging.info("Got unconfirmed_txs. Number: {}".format(len(unconfirmed_txs["result"]["txs"])))
#             RelaysToTokensMultiplier = pokt_rpc.get_param(
#                 "RelaysToTokensMultiplier", height=0)

#             threads = []
#             flat_txs = []

#             for raw_tx in unconfirmed_txs["result"]["txs"]:
#                 x = Request(target=flatten_pending_tx, args=(raw_tx, RelaysToTokensMultiplier))
#                 x.start()
#                 threads.append(x)
            
#             for thread in tqdm(threads):
#                 res = thread.join()

#                 flat_txs.append(res)

#             logging.info("Flattened txs")
#             Transaction.delete().where(Transaction.height == -1).execute()
#             Transaction.insert_many(flat_txs).execute()
            
#             return True
        
#         except Exception as e:
#             logging.warning(
#                 "Mempool failure. Error: {}. Retry-{}".format(e, retries))
#             retries -= 1
#     return False


# def update_pulse(height: int, retries: int = 10):
#     """ update the Pulse section according to models.py

#     height - the height to update pulse at
#     retries - the allowance for an RPC request failure

#     TODO: retries should be inside get_.....
#     """
#     while retries > 0:
#         try:
#             nodes = pokt_rpc.get_nodes(height=height, per_page=1).total_pages
#             apps = pokt_rpc.get_apps(height=height, per_page=1).total_pages

#             pulse = Pulse[1]
#             pulse.nodes = nodes
#             pulse.apps = apps
#             pulse.save()

#             return True
#         except Exception as e:
#             logging.warning(f"Re-try update_pulse {e}", exc_info=True)
#             retries -= 1

#     return False

def sync_block(height: int, retries: int):
    """ add all Transactions of a block and the Block to the database

    height - height to add
    retries - the number of times to retry an RPC request failure

    """

    while retries > 0:
        try:
            RelaysToTokensMultiplier = pokt_rpc.get_param(
                "RelaysToTokensMultiplier", height=height)

            block_header = pokt_rpc.get_block(height).block.header
            timestamp = block_header.time
            proposer = block_header.proposer_address

            logging.info(f"Start gathering transactions for block: {height}")
            block_txs = get_block_txs(height)

            logging.info(f"Flattening transactions for block: {height}")
            flat_txs = [flatten_tx(tx, RelaysToTokensMultiplier, timestamp)
                        for tx in block_txs]
            logging.info(f"Counting relays in block: {height}")
            relays = 0
            for t in flat_txs:
                if t['msg_type'] == "claim":
                    relays += int(t['total_proofs'])

            # logging.info(f"Enreaching transactions with geo data for block: {height}")
            # flat_txs = add_servicer_names(flat_txs)

            logging.info(f"Saving transactions to db, block: {height}")
            Transaction.insert_many(flat_txs).execute()
            Block.create(height=height, proposer=proposer, relays=relays,
                         txs=len(flat_txs), timestamp=timestamp)

            return True
        except Exception as e:
            logging.warning(f"Exception in sync_block: {e}", exc_info=True)
            time.sleep(random.randint(5, 10))
            retries -= 1

    return False


def main():
    state_height = State[1].height
    pokt_height = pokt_rpc.get_height()
    batch_height = pokt_height - (pokt_height % THREADS_NUMBER)
    for batch in range(state_height, batch_height, THREADS_NUMBER):
        logging.info(f"Current height {State[1].height}")

        if quit_event.is_set():
            logging.info("Safely shutting down")
            quit()
        with db.atomic() as transaction:  # Opens new transaction.
            try:
                threads = []
                for block in range(batch, batch + THREADS_NUMBER):
                    if block == 64500:
                        print("June is loaded exiting ............")
                        quit()
                    logging.info(f"Starting block: {block}")
                    x = Request(target=sync_block, args=(block, 10,))
                    x.start()
                    threads.append(x)

                for thread in threads:
                    if thread.join() == False:
                        logging.error("Thread failed, quitting")
                        transaction.rollback()
                        quit()

            except:
                transaction.rollback()
                quit()

            state = State[1]
            state.height = batch + THREADS_NUMBER
            state.save()

            transaction.commit()

    # while True:
    #     # time.sleep(10)
    #     state_height = State[1].height
    #     pokt_height = pokt_rpc.get_height()
    #     # if state_height - 1 == pokt_height:
    #     #     with db.atomic() as transaction:
    #     #         try:
    #     #             logging.info("Updating mempool")
    #     #             update_mempool(20)
    #     #             logging.info("Mempool has been successfully updated")
    #     #         except Exception as e:
    #     #             logging.error("Mempool update has failed {}".format(e))
    #     #             transaction.rollback()
    #     #             quit()

    #     #         transaction.commit()

    #     for block in range(state_height, pokt_height + 1):
    #         logging.info(f"Syncing block: {block}")
    #         if quit_event.is_set():
    #             logging.info("Safely shutting down")
    #             quit()
    #         with db.atomic() as transaction:  # Opens new transaction.
    #             try:
    #                 sync_block(block, 20)
    #                 # update_pulse(block, 20)
    #                 # update_mempool(20)
    #             except Exception as e:
    #                 logging.error(f"Failure to sync block: {e}", exc_info=True)
    #                 transaction.rollback()
    #                 quit()

    #             logging.info(f"Successfully synced block {block}")

    #             transaction.commit()

    #         state = State[1]
    #         state.height = block + 1
    #         state.save()

if __name__ == "__main__":
    main()
