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
    recipient    = CharField(max_length=40, default='')
    msg_type     = CharField(max_length=24)
    total_proofs = IntegerField(null=True)
    fee          = BigIntegerField()
    memo         = TextField()
    amount       = BigIntegerField()
    timestamp    = DateTimeField()
    app_pub_key  = CharField(max_length=64, default='')
    chain        = CharField(max_length=4, default='')
    servicer_pub_key = CharField(max_length=64, default='') # CLAIM/PROOF -> signer == node pub key
    # session_block_height = IntegerField(null=True)
    servicer_url = CharField(max_length=60, default='')
    city         = CharField(max_length=60, default='')
    region       = CharField(max_length=60, default='')
    country      = CharField(max_length=60, default='')
    latitude     = CharField(max_length=15, default='')
    longitude    = CharField(max_length=15, default='')
    org          = CharField(max_length=60, default='')
    isp          = CharField(max_length=60, default='')

    class Meta:
        database=db
        db_table = 'transaction'

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


db.create_tables([Transaction, State, Pulse, Block, GeoCache])

# # POSTgREST setup
# db.execute_sql('grant select on all tables in schema public to {};'.format(os.environ.get("PGRST_DB_ANON_ROLE")))

if Pulse.select().count() == 0:
	Pulse.create(height=0, producer=0, relays=0, txs=0)

if State.select().count() == 0:
	State.create(height=60945)   # =1 To start from 1 block
