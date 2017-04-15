import os
import wlp_utils.etl_utils as etl
import pandas as pd
import datetime
import sqlite3


server_dir = '/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/'
db_dir = server_dir + 'db/'
backups_dir = db_dir + 'backups/'

seed_file_name = db_dir + 'SEED_wgt_steps_cals_2013-01-01_to_2016-12-25.csv'
# seed_file_name = db_dir + 'SEED_wgt_steps_cals_testing.csv'
db_name = 'worldline'
db_ext = '.db'
db_file_name = db_dir + db_name + db_ext

if os.path.isfile(db_file_name):
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
    backup_file_name = backups_dir + db_name + '_BACKUP_' + timestamp + db_ext
    etl.copy_file(db_file_name, backup_file_name)

seed_df = pd.read_csv(seed_file_name, parse_dates=['Date'], index_col='Date')
seed_df.drop(['CaloriesOut', 'CaloriesBMR', 'CaloriesActivity'], axis=1, inplace=True)

conn = sqlite3.connect(db_file_name)
pd.io.sql.to_sql(seed_df, 'fitness', conn, if_exists='replace')



