import shutil
import datetime
import pandas as pd


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
