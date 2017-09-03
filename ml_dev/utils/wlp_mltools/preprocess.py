from wlp_mltools import file_utils
import datetime
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

myfitnesspal_start_date = '2015-09-16'
future_end_date = '2100-01-01'


def _str_to_date(datestring):
    return datetime.datetime.strptime(datestring.split()[0], '%Y-%m-%d')


def _load_fitbit_data(file_path, file_string, json_key, col_name):
    fitbit_data = file_utils.get_json_data(file_path, file_string,
                                           dict_key=json_key)
    fitbit_df = pd.DataFrame(
        [{'DateIndex': _str_to_date(x['dateTime']), col_name: float(x['value'])} for x in fitbit_data])
    fitbit_df = fitbit_df.drop_duplicates('DateIndex', keep='first')
    fitbit_df = fitbit_df.set_index('DateIndex')
    idx = pd.date_range(fitbit_df.index.min(), fitbit_df.index.max())
    fitbit_df = fitbit_df.reindex(idx, fill_value=None)
    return fitbit_df


def _load_calories_consumed():
    calories = file_utils.get_json_data('../_Data/myfitnesspal/', 'myfitnesspaldata')
    calories_df = pd.DataFrame(
        [{'DateIndex': _str_to_date(x['date']), 'Calories': x['totals']['calories']} for x in calories])
    calories_df = calories_df.drop_duplicates('DateIndex', keep='first')
    calories_df = calories_df.set_index('DateIndex')
    idx = pd.date_range(calories_df.index.min(), calories_df.index.max())
    calories_df = calories_df.reindex(idx, fill_value=None)
    return calories_df


def _load_weight():
    askmeevery_data = file_utils.get_csv_data('../_Data/askmeevery/', 'askmeevery_weight')
    askmeevery_df = pd.DataFrame(
        [{'DateIndex': _str_to_date(x['date']), 'Weight': float(x['answer'])} for x in askmeevery_data])
    loggr_data = file_utils.get_csv_data('../_Data/loggr/', 'loggr_weight')
    loggr_df = pd.DataFrame([{'DateIndex': _str_to_date(x['date']), 'Weight': float(x['weight'])} for x in loggr_data])
    withings_data = file_utils.get_csv_data('../_Data/withings/', 'withings_weight.csv')
    withings_data.extend([{'Weight':x['weight'], 'Date':x['date']} for x in file_utils.get_json_data('../_Data/withings/', '.json')])
    withings_df = pd.DataFrame(
        [{'DateIndex': _str_to_date(x['Date']), 'Weight': float(x['Weight'])} for x in withings_data])
    # wrap concat in DataFrame to assist pycharm interpreter
    weight_df = pd.DataFrame(pd.concat([askmeevery_df, loggr_df, withings_df]))
    weight_df = weight_df.drop_duplicates('DateIndex', keep='first')
    weight_df = weight_df.set_index('DateIndex')
    idx = pd.date_range(weight_df.index.min(), weight_df.index.max())
    weight_df = weight_df.reindex(idx, fill_value=None)
    weight_df['Date'] = weight_df.index
    # weight_df = weight_df[weight_df.Date >= food_df.index.min()]
    return weight_df


def load_fitness_data():
    food_df = _load_calories_consumed()
    steps_df = _load_fitbit_data('../_Data/fitbit/activity/daily_steps/', 'daily_steps', 'activities-steps',
                                 'Steps')
    calories_out_df = _load_fitbit_data('../_Data/fitbit/activity/daily_calories/', 'daily_calories_',
                                        'activities-calories', 'CaloriesOut')
    calories_bmr_df = _load_fitbit_data('../_Data/fitbit/activity/daily_calories/', 'daily_caloriesBMR',
                                        'activities-caloriesBMR', 'CaloriesBMR')
    calories_activity_df = _load_fitbit_data('../_Data/fitbit/activity/daily_calories/', 'daily_activityCalories_',
                                             'activities-activityCalories', 'CaloriesActivity')
    fitness_df = _load_weight()
    fitness_df = pd.merge(fitness_df, steps_df, how='left', left_index=True, right_index=True)
    fitness_df = pd.merge(fitness_df, food_df, how='left', left_index=True, right_index=True)
    fitness_df = pd.merge(fitness_df, calories_out_df, how='left', left_index=True, right_index=True)
    fitness_df = pd.merge(fitness_df, calories_bmr_df, how='left', left_index=True, right_index=True)
    fitness_df = pd.merge(fitness_df, calories_activity_df, how='left', left_index=True, right_index=True)
    return fitness_df


def load_weight_data(start_date=myfitnesspal_start_date, end_date=future_end_date):
    interp_range = 7
    fitness_df = load_fitness_data()
    fitness_subset_df = fitness_df[(fitness_df.Date >= datetime.datetime.strptime(start_date, '%Y-%m-%d')) & (
        fitness_df.Date <= datetime.datetime.strptime(end_date, '%Y-%m-%d'))]
    temp = fitness_subset_df[fitness_subset_df.isnull().any(axis=1)].copy()
    temp['Weight'] = 1
    temp = temp.drop(['Steps', 'Date', 'Calories', 'CaloriesOut', 'CaloriesBMR', 'CaloriesActivity'], axis=1).rename(
        columns={"Weight": "WeightImputed"})
    fitness_subset_df = fitness_subset_df.join(temp)
    fitness_subset_df['WeightImputed'] = [1 if val == 1 else 0 for val in fitness_subset_df['WeightImputed']]
    fitness_subset_df = fitness_subset_df.interpolate(limit=interp_range, method='spline', order=5)
    fitness_subset_df['CaloriesDiff'] = fitness_subset_df[['CaloriesOut']].rename(
        columns={"CaloriesOut": "Calories"}) - fitness_subset_df[['Calories']]
    return fitness_subset_df


def reshape_sequences_target_scalar(data_in, sequence_length):
    n_features = data_in.shape[1]
    features = []
    target = []
    for i in range(len(data_in) - sequence_length):
        x = data_in[i:(i + sequence_length), 0:n_features]
        features.append(x)
        y = np.array([data_in[i + sequence_length, 0]])
        target.append(y)
    return np.array(features), np.array(target)


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


def _get_data0(weight_transform,
               steps_transform,
               calories_transform, start_date=myfitnesspal_start_date, end_date=future_end_date):
    modeldata_df = load_weight_data(start_date=start_date, end_date=end_date)
    modeldata_df.drop(['Date', 'CaloriesOut', 'CaloriesBMR', 'CaloriesActivity', 'WeightImputed', 'CaloriesDiff'],
                      axis=1, inplace=True)
    modeldata_df.Weight = weight_transform(modeldata_df[['Weight']])
    modeldata_df.Steps = steps_transform(modeldata_df[['Steps']])
    modeldata_df.Calories = calories_transform(modeldata_df[['Calories']])
    return modeldata_df


def get_data(sequence_length, train_fraction,
             weight_transform,
             steps_transform,
             calories_transform,
             random_seed=None, start_date=myfitnesspal_start_date, end_date=future_end_date):
    val_fraction = 1 - train_fraction
    modeldata_df = _get_data0(weight_transform, steps_transform, calories_transform,
                              start_date=start_date, end_date=end_date)

    modeldata = modeldata_df.as_matrix()
    data_x, data_y = reshape_sequences_target_sequence(modeldata, sequence_length)

    X_train, X_val, Y_train, Y_val = train_test_split(data_x, data_y, test_size=val_fraction, random_state=random_seed)

    # trainIndexMax = int(data_x.shape[0] * train_fraction)
    # valIndexMax = data_x.shape[0]
    #
    # X_train = data_x[0:trainIndexMax]
    # Y_train = data_y[0:trainIndexMax]
    # X_val = data_x[(trainIndexMax + 1):valIndexMax]
    # Y_val = data_y[(trainIndexMax + 1):valIndexMax]

    return X_train, Y_train, X_val, Y_val


def get_noisy_data(sequence_length, train_fraction,
                   weight_transform,
                   steps_transform,
                   calories_transform,
                   rel_err_weight,
                   rel_err_steps,
                   rel_err_calories):
    val_fraction = 1 - train_fraction
    modeldata_df = _get_data0(sequence_length, train_fraction, weight_transform, steps_transform, calories_transform)
    modeldata_df.Weight = (lambda x: np.random.normal(x, x * rel_err_weight))(modeldata_df[['Weight']])
    modeldata_df.Steps = (lambda x: np.random.normal(x, x * rel_err_steps))(modeldata_df[['Steps']])
    modeldata_df.Calories = (lambda x: np.random.normal(x, x * rel_err_calories))(modeldata_df[['Calories']])

    modeldata = modeldata_df.as_matrix()
    data_x, data_y = reshape_sequences_target_sequence(modeldata, sequence_length)

    X_train, X_val, Y_train, Y_val = train_test_split(data_x, data_y, test_size=val_fraction)  # , random_state=42)

    # trainIndexMax = int(data_x.shape[0] * train_fraction)
    # valIndexMax = data_x.shape[0]
    #
    # X_train = data_x[0:trainIndexMax]
    # Y_train = data_y[0:trainIndexMax]
    # X_val = data_x[(trainIndexMax + 1):valIndexMax]
    # Y_val = data_y[(trainIndexMax + 1):valIndexMax]

    return X_train, Y_train, X_val, Y_val
