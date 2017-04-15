import wlp_utils.etl_utils as etl
import os
import datetime
import ConfigParser
import sqlite3
import pandas as pd
from withings import WithingsApi, WithingsCredentials

server_dir = '/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/'
cfg_file = server_dir + 'config/api_params.cfg'
db_dir = server_dir + 'db/'
backups_dir = db_dir + 'backups/'
db_name = 'worldline'
db_ext = '.db'
db_file_name = db_dir + db_name + db_ext

conn = sqlite3.connect(db_file_name)
db_df = pd.io.sql.read_sql_table('fitness', 'sqlite:///' + db_file_name, index_col='Date', parse_dates=['Date'])

parser = ConfigParser.SafeConfigParser()
parser.read(cfg_file)
consumer_key = parser.get('withings', 'consumer_key')
consumer_secret = parser.get('withings', 'consumer_secret')
access_token = parser.get('withings', 'access_token')
access_token_secret = parser.get('withings', 'access_token_secret')
user_id = parser.get('withings', 'user_id')

creds = WithingsCredentials(access_token=access_token,
                            access_token_secret=access_token_secret,
                            consumer_key=consumer_key,
                            consumer_secret=consumer_secret,
                            user_id=user_id)

client = WithingsApi(creds)

[date_start, date_end] = etl.get_target_date_endpoints('Weight', db_df)
date_query = date_start
date_diff = date_end - date_query
days = date_diff.days+2

measures = client.get_measures(meastype=1, limit=days)
measures.pop(0)
weight_json = [{'weight':(float("{:.1f}".format(x.weight*2.20462))), 'date':x.date.strftime('%Y-%m-%d')} for x in measures]
dvals = [[pd.tseries.tools.to_datetime(x['date']), x['weight']] for x in weight_json]
updated_df = etl.insert_values(dvals, 'Weight', db_df)

if os.path.isfile(db_file_name):
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
    backup_file_name = backups_dir + db_name + '_BACKUP_' + timestamp + db_ext
    etl.copy_file(db_file_name, backup_file_name)

pd.io.sql.to_sql(updated_df, 'fitness', conn, if_exists='replace')


