import shutil
import datetime
import numpy as np
import pandas as pd
import ConfigParser
import fitbit
import myfitnesspal
from withings import WithingsApi, WithingsCredentials


def copy_file(src, dest):
    try:
        shutil.copy(src, dest)
    # eg. src and dest are the same file
    except shutil.Error as e:
        print('Error: %s' % e)
    # eg. source or destination doesn't exist
    except IOError as e:
        print('Error: %s' % e.strerror)


def get_latest_date(column, df):
    df_filtered = pd.DataFrame(df.loc[df[column] > 0], copy=True)
    df_filtered.sort_index(ascending=False, inplace=True)
    return df_filtered.iloc[0].name


def get_target_date_endpoints(column, df):
    today = datetime.date.today()
    today = datetime.datetime.combine(today, datetime.datetime.min.time())
    latest_date = get_latest_date(column, df)
    first_date = latest_date + datetime.timedelta(days=1)
    first_date = datetime.datetime.combine(first_date.date(), datetime.datetime.min.time())
    last_date = today - datetime.timedelta(days=1)
    return [first_date, last_date]


def get_target_date_range(column, df):
    [first_date, last_date] = get_target_date_endpoints(column, df)
    target_dates = pd.date_range(first_date, last_date).values
    return [pd.to_datetime(d) for d in target_dates]


def insert_values(date_values, column, df):
    df_updated = pd.DataFrame(df, copy=True)
    for dv in date_values:
        df_updated.set_value(dv[0], column, dv[1])
    return df_updated


def persist_fitbit_refresh_token(token_dict, cfg_file):
    parser = ConfigParser.SafeConfigParser()
    parser.read(cfg_file)
    parser.set('fitbit', 'access_token', token_dict['access_token'])
    parser.set('fitbit', 'refresh_token', token_dict['refresh_token'])
    parser.set('fitbit', 'expires_at', "{:.6f}".format(token_dict['expires_at']))
    with open(cfg_file, 'wb') as configfile:
        parser.write(configfile)


def refresh_steps(cfg_file, db_connection, db_df):
    print "REFRESHING STEPS..."
    parser = ConfigParser.SafeConfigParser()
    parser.read(cfg_file)
    consumer_key = parser.get('fitbit', 'consumer_key')
    consumer_secret = parser.get('fitbit', 'consumer_secret')
    access_token = parser.get('fitbit', 'access_token')
    refresh_token = parser.get('fitbit', 'refresh_token')
    expires_at = parser.get('fitbit', 'expires_at')

    auth_client = fitbit.Fitbit(consumer_key, consumer_secret,
                                access_token=access_token,
                                refresh_token=refresh_token,
                                expires_at=float(expires_at),
                                refresh_cb=(lambda x: persist_fitbit_refresh_token(x, cfg_file))
                                )

    [date_start, date_end] = get_target_date_endpoints('Steps', db_df)
    steps = auth_client.time_series('activities/steps', base_date=date_start, end_date=date_end)
    date_values = [[pd.tseries.offsets.to_datetime(val['dateTime']), val['value']] for val in steps['activities-steps']]
    updated_df = insert_values(date_values, 'Steps', db_df)
    updated_df[['Steps']] = updated_df[['Steps']].apply(pd.to_numeric)

    pd.io.sql.to_sql(updated_df, 'fitness', db_connection, if_exists='replace')

    return updated_df


def refresh_calories(db_connection, db_df):
    print "REFRESHING CALORIES..."
    [date_start, date_end] = get_target_date_endpoints('Calories', db_df)
    date_query = date_start
    date_diff = date_end - date_query
    days = date_diff.days + 1

    client = myfitnesspal.Client('jamieinfinity')

    diary_dump = []
    for i in range(days):
        diary_data = client.get_date(date_query)
        diary_dump.append(diary_data)
        date_query = date_query + datetime.timedelta(days=1)

    date_values = [[pd.tseries.offsets.to_datetime(x.date.strftime('%Y-%m-%d')), x.totals['calories']] for x in
                   diary_dump]

    updated_df = insert_values(date_values, 'Calories', db_df)

    pd.io.sql.to_sql(updated_df, 'fitness', db_connection, if_exists='replace')

    return updated_df


def refresh_weight(cfg_file, db_connection, db_df):
    print "REFRESHING WEIGHT..."
    parser = ConfigParser.SafeConfigParser()
    parser.read(cfg_file)
    consumer_key = parser.get('withings', 'consumer_key')
    consumer_secret = parser.get('withings', 'consumer_secret')
    access_token = parser.get('withings', 'access_token')
    access_token_secret = parser.get('withings', 'access_token_secret')
    user_id = parser.get('withings', 'user_id')

    credentials = WithingsCredentials(access_token=access_token,
                                      access_token_secret=access_token_secret,
                                      consumer_key=consumer_key,
                                      consumer_secret=consumer_secret,
                                      user_id=user_id)
    client = WithingsApi(credentials)

    [date_start, date_end] = get_target_date_endpoints('Weight', db_df)
    date_query = date_start
    date_diff = date_end - date_query
    days = date_diff.days + 2

    measures = client.get_measures(meastype=1, limit=days)
    measures.pop(0)
    weight_json = [{'weight': (float("{:.1f}".format(x.weight * 2.20462))), 'date': x.date.strftime('%Y-%m-%d')} for x
                   in measures]
    date_values = [[pd.tseries.offsets.to_datetime(x['date']), x['weight']] for x in weight_json]
    updated_df = insert_values(date_values, 'Weight', db_df)

    pd.io.sql.to_sql(updated_df, 'fitness', db_connection, if_exists='replace')

    return updated_df


def impute_missing_weights(db_connection, db_df):
    print "IMPUTING MISSING WEIGHTS..."

    generated_columns = [col for col in db_df.columns.values if
                         col not in ['Weight', 'Steps', 'Calories', 'WeightImputed']]
    db_df_copy = db_df.copy()
    db_df_copy.drop(generated_columns, axis=1, inplace=True)
    interp_range = 8
    temp = db_df_copy[(db_df_copy['Weight'].isnull()) | (db_df_copy['WeightImputed'] == 1)].copy()
    temp['Weight'] = 1
    temp = temp.drop(['Steps', 'Calories', 'WeightImputed'], axis=1).rename(
        columns={"Weight": "WeightImputed"})
    db_df_copy.drop(["WeightImputed"], axis=1, inplace=True)
    db_df_copy = db_df_copy.join(temp)
    db_df_copy['WeightImputed'] = [1 if val == 1 else 0 for val in db_df_copy['WeightImputed']]
    db_df_copy2 = db_df_copy.copy()
    db_df_copy2 = db_df_copy2.interpolate(limit=interp_range, method='spline', order=5)
    db_df_copy.Weight = db_df_copy2.Weight.values

    pd.io.sql.to_sql(db_df_copy, 'fitness', db_connection, if_exists='replace')

    return db_df_copy


def kernel_function(x, radius):
    return np.exp(-(x ** 2) / (2 * radius ** 2)) / (np.sqrt(2 * np.pi) * radius)


def date_diff_days(d1, d2):
    return (d2 - d1).astype('timedelta64[D]').astype(int)


def zeroify(x):
    return x if not np.isnan(x) else 0


def select_null(x_orig, x_new):
    return x_new if not np.isnan(x_orig) else x_orig


def smooth0(index, x, val, radius):
    numerator = [zeroify(val[i]) * kernel_function(x[index] - x[i], radius) for i in range(0, len(x))]
    denominator = [kernel_function(x[index] - x[i], radius) for i in range(0, len(x))]
    return np.sum(numerator) / np.sum(denominator)


def data_smoother(data, radius, diff_op):
    x1 = data[0][0]
    x = [diff_op(x1, di[0]) for di in data]
    val = [di[1] for di in data]
    smooth_vals = [smooth0(i, x, val, radius) for i in range(0, len(data))]
    smooth_vals = [select_null(val[i], smooth_vals[i]) for i in range(0, len(data))]
    return [[data[i][0], smooth_vals[i]] for i in range(0, len(data))]


def add_smoothed_col(db_df, col, radius):
    new_col_name = col + 'Smoothed' + str(radius) + 'Days'
    xi = db_df.index.values
    vals = db_df[col].values
    xv = [[xi[i], vals[i]] for i in range(0, len(vals))]
    xv_smoothed = data_smoother(xv, radius, date_diff_days)
    xv_smoothed = data_smoother(xv_smoothed, radius, date_diff_days)
    db_df[new_col_name] = [xv[1] for xv in xv_smoothed]


def add_smoothed_cols(db_connection, db_df):
    db_df_copy = db_df.copy()
    print "ADDING SMOOTHED STEPS..."
    add_smoothed_col(db_df_copy, 'Steps', 3)
    add_smoothed_col(db_df_copy, 'Steps', 5)
    add_smoothed_col(db_df_copy, 'Steps', 7)
    print "ADDING SMOOTHED WEIGHT..."
    add_smoothed_col(db_df_copy, 'Weight', 3)
    add_smoothed_col(db_df_copy, 'Weight', 5)
    add_smoothed_col(db_df_copy, 'Weight', 7)
    print "ADDING SMOOTHED CALORIES..."
    add_smoothed_col(db_df_copy, 'Calories', 3)
    add_smoothed_col(db_df_copy, 'Calories', 5)
    add_smoothed_col(db_df_copy, 'Calories', 7)

    pd.io.sql.to_sql(db_df_copy, 'fitness', db_connection, if_exists='replace')

    return db_df_copy
