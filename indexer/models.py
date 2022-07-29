from ipaddress import ip_address
from peewee import *
import os
import time
# give time for db to warm up
# time.sleep(10)
db = PostgresqlDatabase(user     = os.environ.get('POSTGRES_USER'),
                        database = os.environ.get('POSTGRES_DB'),
                        host     = os.environ.get('POSTGRES_NAME'),
                        password = os.environ.get("POSTGRES_PASSWORD"),
                        port     = os.environ.get('POSTGRES_PORT', '5432'))

class Block(Model):
    height = IntegerField(null=True) #unique=True
    proposer = CharField(max_length=40, null=True)
    relays = IntegerField(null=True)
    txs = IntegerField(null=True)
    timestamp = DateTimeField()

    class Meta:
        database=db
        db_table = 'block'

class Pulse(Model):
    relays = BigIntegerField(null=True)
    nodes = IntegerField(null=True)
    apps = IntegerField(null=True)
    # id = IntegerField(null=True)

    class Meta:
        database=db
        db_table = 'pulse'

class State(Model):
    height = IntegerField(null=True)

    class Meta:
        database=db
        db_table = 'state'

class Transaction(Model):
    height       = IntegerField()
    index        = IntegerField()
    hash         = CharField(max_length=64) #unique=True
    result_code  = IntegerField()
    signer       = CharField(max_length=40) # CLAIM,PROOF: signer==NODE_ADDRESS
    recipient    = CharField(max_length=40, default=None, null=True)
    msg_type     = CharField(max_length=24)
    total_proofs = IntegerField(default=None, null=True)
    fee          = BigIntegerField()
    memo         = TextField()
    amount       = BigIntegerField()
    timestamp    = DateTimeField()
    app_pub_key  = CharField(max_length=64, default=None, null=True)
    chain        = CharField(max_length=4, default=None, null=True)
    servicer_pub_key = CharField(max_length=64, default='') # CLAIM/PROOF -> signer == node pub key
    # session_block_height = IntegerField(null=True)
    servicer_url = CharField(max_length=60, default=None, null=True)
    city         = CharField(max_length=60, default=None, null=True)
    region       = CharField(max_length=60, default=None, null=True)
    country      = CharField(max_length=60, default=None, null=True)
    latitude     = CharField(max_length=15, default=None, null=True)
    longitude    = CharField(max_length=15, default=None, null=True)
    org          = CharField(max_length=60, default=None, null=True)
    isp          = CharField(max_length=60, default=None, null=True)

    class Meta:
        database=db
        db_table = 'transaction'


# class ServicersCache(Model):
#     node_address = CharField(max_length=40, unique = True)
#     height = IntegerField()

#     service_url = CharField(max_length=60, null=True)
#     city = CharField(max_length=60, null=True)
#     region = CharField(max_length=60, null=True)
#     country = CharField(max_length=60, null=True)
#     latitude = CharField(max_length=15, null=True)
#     longitude = CharField(max_length=15, null=True)
#     org = CharField(max_length=60, null=True)
#     isp = CharField(max_length=60, null=True)

#     class Meta:
#         database=db
#         db_table = 'servicerscache'

class GeoCache(Model):
    ip_address = CharField(max_length=15, unique = True)    #XXX.XXX.XXX.XXX
    timestamp = BigIntegerField()
    city = CharField(max_length=60, null=True)
    region = CharField(max_length=60, null=True)
    country = CharField(max_length=60, null=True)
    latitude = CharField(max_length=15, null=True)
    longitude = CharField(max_length=15, null=True)
    org = CharField(max_length=60, null=True)
    isp = CharField(max_length=60, null=True)

    class Meta:
        database=db
        db_table = 'geocache'

class Chains(Model):
    chain = CharField(max_length=4, unique = True)
    name = CharField(max_length=50, null=True)

    class Meta:
        database=db
        db_table = 'chains'

db.create_tables([Transaction, State, Block, GeoCache, Chains]) # Pulse,

# Populate chains
supported_chains=[
        {"name": "Algorand", "chain":"0029"},
        {"name": "Avalanche", "chain": "0003"},
        {"name": "Binance Smart Chain", "chain": "0004"},
        {"name": "Binance Smart Chain Archival", "chain": "0010"},
        {"name": "Boba", "chain": "0048"},
        {"name": "DFKchain Subnet", "chain": "03DF"},
        {"name": "Evmos", "chain": "0046"},
        {"name": "Ethereum", "chain": "0021"},
        {"name": "Ethereum Archival", "chain": "0022"},
        {"name": "Ethereum Archival Trace", "chain": "0028"},
        {"name": "Ethereum Goerli", "chain": "0026"},
        {"name": "Ethereum Kovan", "chain": "0024"},
        {"name": "Ethereum Rinkeby", "chain": "0025"},
        {"name": "Ethereum Ropsten", "chain": "0023"},
        {"name": "Fantom", "chain": "0049"},
        {"name": "FUSE", "chain": "0005"},
        {"name": "FUSE Archival", "chain": "000A"},
        {"name": "Gnosis Chain", "chain": "0027"},
        {"name": "Gnosis Chain Archival", "chain": "000C"},
        {"name": "Harmony Shard 0", "chain": "0040"},
        {"name": "IoTeX", "chain": "0044"},
        {"name": "Moonbeam", "chain": "0050"},
        {"name": "Moonriver", "chain": "0051"},
        {"name": "NEAR", "chain": "0052"},
        {"name": "OKExChain", "chain": "0047"},
        {"name": "Optimism", "chain": "0053"},
        {"name": "Pocket Network", "chain": "0001"},
        {"name": "Polygon", "chain": "0009"},
        {"name": "Polygon Archival", "chain": "000B"},
        {"name": "Solana", "chain": "0006"},
        {"name": "Swimmer Network Mainnet", "chain": "03CB"},
        {"name": "Osmosis Mainnet", "chain": "0054"},
        {"name": "BSC Testnet Archival", "chain": "0012"}
    ]
# q=Chains.insert_many(supported_chains).execute()

# # POSTgREST setup
# db.execute_sql('grant select on all tables in schema public to {};'.format(os.environ.get("PGRST_DB_ANON_ROLE")))

# if Pulse.select().count() == 0:
# 	Pulse.create(height=0, producer=0, relays=0, txs=0)

if State.select().count() == 0:
	State.create(height=60945)   # =1 To start from 1 block
