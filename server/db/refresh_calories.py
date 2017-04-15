import wlp_utils.etl_utils as etl
import os
import datetime
import sqlite3
import pandas as pd
import myfitnesspal

server_dir = '/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/'
cfg_file = server_dir + 'config/api_params.cfg'
db_dir = server_dir + 'db/'
backups_dir = db_dir + 'backups/'
db_name = 'worldline'
db_ext = '.db'
db_file_name = db_dir + db_name + db_ext

conn = sqlite3.connect(db_file_name)
db_df = pd.io.sql.read_sql_table('fitness', 'sqlite:///'+db_file_name, index_col='Date', parse_dates=['Date'])

[date_start, date_end] = etl.get_target_date_endpoints('Calories', db_df)
date_query = date_start
date_diff = date_end - date_query
days = date_diff.days+1

client = myfitnesspal.Client('jamieinfinity')

diary_dump = []
for i in range(days):
    diary_data = client.get_date(date_query)
    diary_dump.append(diary_data)
    date_query = date_query + datetime.timedelta(days=1)

dvals = [[pd.tseries.tools.to_datetime(x.date.strftime('%Y-%m-%d')), (x.totals)['calories']] for x in diary_dump]

updated_df = etl.insert_values(dvals, 'Calories', db_df)

if os.path.isfile(db_file_name):
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
    backup_file_name = backups_dir + db_name + '_BACKUP_' + timestamp + db_ext
    etl.copy_file(db_file_name, backup_file_name)

pd.io.sql.to_sql(updated_df, 'fitness', conn, if_exists='replace')


