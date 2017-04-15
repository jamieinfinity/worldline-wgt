import wlp_utils.etl_utils as etl
import os
import datetime
import ConfigParser
import sqlite3
import pandas as pd
import fitbit

server_dir = '/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/'
cfg_file = server_dir + 'config/api_params.cfg'
db_dir = server_dir + 'db/'
backups_dir = db_dir + 'backups/'
db_name = 'worldline'
db_ext = '.db'
db_file_name = db_dir + db_name + db_ext


def persist_refresh_token(token_dict):
    parser = ConfigParser.SafeConfigParser()
    parser.read(cfg_file)
    parser.set('fitbit', 'access_token', token_dict['access_token'])
    parser.set('fitbit', 'refresh_token', token_dict['refresh_token'])
    parser.set('fitbit', 'expires_at', "{:.6f}".format(token_dict['expires_at']))
    with open(cfg_file, 'wb') as configfile:
        parser.write(configfile)

conn = sqlite3.connect(db_file_name)
db_df = pd.io.sql.read_sql_table('fitness', 'sqlite:///'+db_file_name, index_col='Date', parse_dates=['Date'])

parser = ConfigParser.SafeConfigParser()
parser.read(cfg_file)
consumer_key = parser.get('fitbit', 'consumer_key')
consumer_secret = parser.get('fitbit', 'consumer_secret')
access_token = parser.get('fitbit', 'access_token')
refresh_token = parser.get('fitbit', 'refresh_token')
expires_at = parser.get('fitbit', 'expires_at')

authd_client = fitbit.Fitbit(consumer_key, consumer_secret,
                             access_token=access_token,
                             refresh_token=refresh_token,
                             expires_at=float(expires_at),
                             refresh_cb = persist_refresh_token)

[startdate, enddate] = etl.get_target_date_endpoints('Steps', db_df)
steps = authd_client.time_series('activities/steps', base_date=startdate, end_date=enddate)
dvals = [[pd.tseries.tools.to_datetime(val['dateTime']), val['value']] for val in steps['activities-steps']]
updated_df = etl.insert_values(dvals, 'Steps', db_df)

if os.path.isfile(db_file_name):
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
    backup_file_name = backups_dir + db_name + '_BACKUP_' + timestamp + db_ext
    etl.copy_file(db_file_name, backup_file_name)

pd.io.sql.to_sql(updated_df, 'fitness', conn, if_exists='replace')



