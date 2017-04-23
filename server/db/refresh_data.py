#!/Users/jamieinfinity/anaconda/envs/py27/bin/python
# import sys
# toolpath = '/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/src'
# sys.path.append(toolpath)
import wlp_utils.etl_utils as etl
import os
import datetime
import sqlite3
import pandas as pd


server_dir = '/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/'
cfg_file = server_dir + 'config/api_params.cfg'
db_dir = server_dir + 'db/'
backups_dir = db_dir + 'backups/'
db_name = 'worldline'
db_ext = '.db'
db_file_name = db_dir + db_name + db_ext

db_connection = sqlite3.connect(db_file_name)
db_df = pd.io.sql.read_sql_table('fitness', 'sqlite:///'+db_file_name, index_col='Date', parse_dates=['Date'])

if os.path.isfile(db_file_name):
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
    backup_file_name = backups_dir + db_name + '_BACKUP_' + timestamp + db_ext
    etl.copy_file(db_file_name, backup_file_name)

updated_df = etl.refresh_steps(cfg_file, db_connection, db_df)
updated_df = etl.refresh_weight(cfg_file, db_connection, updated_df)
updated_df = etl.refresh_calories(db_connection, updated_df)
updated_df = etl.impute_missing_weights(db_connection, updated_df)
updated_df = etl.add_smoothed_cols(db_connection, updated_df)

