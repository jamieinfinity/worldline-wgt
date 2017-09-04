from sqlalchemy import create_engine
import datetime
import pandas as pd
import numpy as np


server_dir = '/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/'
cfg_file = server_dir + 'config/api_params.cfg'
db_dir = server_dir + 'db/'
backups_dir = db_dir + 'backups/'
db_name = 'worldline'
db_ext = '.db'
db_file_name = db_dir + db_name + db_ext

_engine = create_engine('sqlite:///'+db_file_name)

with _engine.connect() as conn, conn.begin():
    _db_df = pd.read_sql_table('fitness', conn, index_col='Date', parse_dates=['Date'])


def weight_transform(w):
    return (w - 150.)/50.


def steps_transform(s):
    return s/40000.


def calories_transform(c):
    return (c-500.)/4000.


def weight_inverse_transform(w):
    return w*50+150.


def steps_inverse_transform(s):
    return s*40000.


def calories_inverse_transform(c):
    return c*4000. + 500.


def reshape_sequences_target_sequence(data_in, sequence_length):
    n_features = data_in.shape[1]
    features = []
    target = []
    for i in range(len(data_in) - sequence_length):
        x = data_in[i:(i + sequence_length), 0:n_features]
        features.append(x)
        y = data_in[i + 1:(i + sequence_length + 1), 0]
        target.append([np.array([yi]) for yi in y])
    return np.array(features), np.array(target)


def get_model_data_df(start_date_str, end_date_str):
    date_start = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    date_end = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
    model_data_df = _db_df[(_db_df.index.to_pydatetime() >= date_start) & (_db_df.index.to_pydatetime() <= date_end)]
    model_data_df = model_data_df[['Weight', 'Steps', 'Calories']]
    return model_data_df


def get_model_data_seq(start_date_str, end_date_str, sequence_length):
    model_data = get_model_data_df(start_date_str, end_date_str)
    model_data.Weight = weight_transform(model_data[['Weight']])
    model_data.Steps = steps_transform(model_data[['Steps']])
    model_data.Calories = calories_transform(model_data[['Calories']])
    return reshape_sequences_target_sequence(model_data.as_matrix(), sequence_length)