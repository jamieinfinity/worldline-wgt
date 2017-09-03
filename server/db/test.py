#!/Users/jamieinfinity/anaconda/bin/python3

import sys
toolpath = '/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/src'
sys.path.append(toolpath)
import wlp_utils.etl_utils as etl
import os
import datetime
import sqlite3
import pandas as pd

#import configparser
# import fitbit
# from withings import WithingsApi, WithingsCredentials

#server_dir = '/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/'
#cfg_file = server_dir + 'config/api_params.cfg'

# parser = configparser.ConfigParser()
# parser.read(cfg_file)
# consumer_key = parser.get('withings', 'consumer_key')
# consumer_secret = parser.get('withings', 'consumer_secret')
# access_token = parser.get('withings', 'access_token')
# access_token_secret = parser.get('withings', 'access_token_secret')
# user_id = parser.get('withings', 'user_id')
#
# credentials = WithingsCredentials(access_token=access_token,
#                                   access_token_secret=access_token_secret,
#                                   consumer_key=consumer_key,
#                                   consumer_secret=consumer_secret,
#                                   user_id=user_id)
# client = WithingsApi(credentials)
# measures = client.get_measures(meastype=1, limit=3)
# this = [x.weight for x in measures]
# print(str(this))



# def persist_fitbit_refresh_token(token_dict, cfg_file):
#     parser = configparser.ConfigParser()
#     parser.read(cfg_file)
#     parser.set('fitbit', 'access_token', token_dict['access_token'])
#     parser.set('fitbit', 'refresh_token', token_dict['refresh_token'])
#     parser.set('fitbit', 'expires_at', "{:.6f}".format(token_dict['expires_at']))
#     with open(cfg_file, 'wb') as configfile:
#         parser.write(configfile)
#
#
# def test_fitbit(cfg_file):
#     parser = configparser.ConfigParser()
#     parser.read(cfg_file)
#     consumer_key = parser.get('fitbit', 'consumer_key')
#     consumer_secret = parser.get('fitbit', 'consumer_secret')
#     access_token = parser.get('fitbit', 'access_token')
#     refresh_token = parser.get('fitbit', 'refresh_token')
#     expires_at = parser.get('fitbit', 'expires_at')
#
#     auth_client = fitbit.Fitbit(consumer_key, consumer_secret,
#                                 access_token=access_token,
#                                 refresh_token=refresh_token,
#                                 expires_at=float(expires_at),
#                                 refresh_cb=(lambda x: persist_fitbit_refresh_token(x, cfg_file))
#                                 )
#     ts = auth_client.time_series('activities/steps', period='7d')
#     print(str(ts))
#
#
# test_fitbit(cfg_file)




# import myfitnesspal
#
# client = myfitnesspal.Client('jamieinfinity')
#
# data = client.get_date(2017, 8, 30)
#
# f1=open('/Users/jamieinfinity/Projects/WorldLine/worldline-wgt/server/db/testoutput.dat', 'w+')
# f1.write(str(data))
# f1.close()


# /Users/jamieinfinity/anaconda/envs/py27/bin/python
