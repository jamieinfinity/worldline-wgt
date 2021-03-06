from sqlalchemy import create_engine
import datetime
import pandas as pd
import numpy as np
import random
from sklearn.model_selection import KFold
from keras.layers import Input
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import TimeDistributed
from keras.models import Model
from keras.callbacks import EarlyStopping

earliest_date = '2015-09-16'
server_dir = '/Users/jamieinfinity/Dropbox/Projects/WorldLine/worldline-wgt/server/'
cfg_file = server_dir + 'config/api_params.cfg'
db_dir = server_dir + 'db/'
backups_dir = db_dir + 'backups/'
db_name = 'worldline'
db_ext = '.db'
db_file_name = db_dir + db_name + db_ext

_engine = create_engine('sqlite:///' + db_file_name)

with _engine.connect() as conn, conn.begin():
    _db_df = pd.read_sql_table('fitness', conn, index_col='Date', parse_dates=['Date'])


def weight_transform(w):
    return w / 170.0
#    return (w - 150.) / 50.


def steps_transform(s):
    return s / 12000.0
#    return s / 40000.


def calories_transform(c):
    return c / 2000.0
#    return (c - 500.) / 4000.


def weight_inverse_transform(w):
    return w * 170.0
#    return w * 50 + 150.


def steps_inverse_transform(s):
    return s * 12000.0
#    return s * 40000.


def calories_inverse_transform(c):
    return c * 2000.0
#    return c * 4000. + 500.


def reshape_sequences_target_sequence(model_data_df, sequence_length, shuffle=False):
    data_in = model_data_df.as_matrix()
    dates_in = model_data_df.index
    n_features = data_in.shape[1]
    features = []
    target = []
    dates = []
    for i in range(len(data_in) - sequence_length):
        x = data_in[i:(i + sequence_length), 0:n_features]
        features.append(x)
        d = dates_in[i:(i + sequence_length)]
        dates.append(d)
        y = data_in[i + 1:(i + sequence_length + 1), 0]
        target.append([np.array([yi]) for yi in y])
    if shuffle:
        inds = list(range(len(features)))
        random.shuffle(inds)
        features = [features[i] for i in inds]
        dates = [dates[i] for i in inds]
        target = [target[i] for i in inds]
    return np.array(features), np.array(target), np.array(dates)


def get_model_data_df(start_date_str, end_date_str):
    date_start = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    date_end = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
    model_data_df = _db_df[(_db_df.index.to_pydatetime() >= date_start) & (_db_df.index.to_pydatetime() <= date_end)]
    model_data_df = model_data_df[['Weight', 'Steps', 'Calories']]
    return model_data_df


def get_model_data_seq(start_date_str, end_date_str, sequence_length, shuffle=False):
    model_data_df = get_model_data_df(start_date_str, end_date_str)
    model_data_df.Weight = weight_transform(model_data_df[['Weight']])
    model_data_df.Steps = steps_transform(model_data_df[['Steps']])
    model_data_df.Calories = calories_transform(model_data_df[['Calories']])
    return reshape_sequences_target_sequence(model_data_df, sequence_length, shuffle)


def get_model_data_splits(sequence_length=10, holdout_days=60, test_days=60, train_shuffle=False):
    data_df = get_model_data_df(earliest_date, '2020-01-01')
    max_date_holdout = np.max(data_df.index)
    max_date_holdout.to_datetime
    max_date_holdout_str = max_date_holdout.date().isoformat()
    min_date_holdout = max_date_holdout - datetime.timedelta(days=holdout_days)
    if holdout_days == 0:
        min_date_holdout = max_date_holdout
    min_date_holdout_str = min_date_holdout.date().isoformat()
    min_date_test = min_date_holdout - datetime.timedelta(days=test_days)
    min_date_test_str = min_date_test.date().isoformat()
    train_val = get_model_data_seq(earliest_date, min_date_test_str, sequence_length, shuffle=train_shuffle)
    test = get_model_data_seq(min_date_test_str, min_date_holdout_str, sequence_length, shuffle=False)
    if holdout_days == 0:
        holdout=(np.array([]), np.array([]), np.array([]))
    else:
        holdout = get_model_data_seq(min_date_holdout_str, max_date_holdout_str, sequence_length, shuffle=False)
    return [train_val, test, holdout]


def build_lstm_layer(lstm_size, dropout_rate, previous_layer):
    layer_lstm = LSTM(lstm_size, activation='relu', return_sequences=True)(previous_layer)
    layer_dropout = Dropout(dropout_rate)(layer_lstm)
    return layer_dropout


def build_lstm_layers(lstm_sizes, dropout_rates, previous_layer):
    prior_layers = [previous_layer]
    for i in range(len(lstm_sizes)):
        new_layer = build_lstm_layer(lstm_sizes[i], dropout_rates[i], prior_layers[-1])
        prior_layers.append(new_layer)
    return prior_layers[-1]


def build_lstm_model(model_params):
    _layer_input = Input(shape=(model_params['sequence_length'], model_params['num_features']))
    _layer_lstm_final = build_lstm_layers(model_params['lstm_sizes'], model_params['lstm_dropout_rates'], _layer_input)
    _layer_output = TimeDistributed(Dense(1, activation='linear'))(_layer_lstm_final)
    model = Model(inputs=[_layer_input], outputs=[_layer_output])
    return model


def train_model(model_params, training_params, data):
    [(X_train, y_train), (X_val, y_val)] = data
    model = build_lstm_model(model_params)
    model.compile(loss=training_params['loss_function'], optimizer=training_params['optimization_method'])
    early_stopping = EarlyStopping(monitor='val_loss', patience=training_params['early_stopping_patience'],
                                   min_delta=training_params['min_delta'])

    hist = model.fit(X_train, y_train, validation_data=(X_val, y_val),
                     batch_size=training_params['batch_size'],
                     epochs=training_params['epochs'], verbose=training_params['verboseness'],
                     callbacks=[early_stopping])

    return model, hist


def train_cv_models(model_params, training_params, data, n_splits=5, random_state=42, early_stopping_data=None):
    [(features_train, target_train), (features_test, target_test)] = data
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    models = []
    histories = []
    losses = []
    cv_indices = []
    fold = 0
    for train_index, val_index in kfold.split(features_train):
        print('Fold %d ' % fold)
        cv_indices.append((train_index, val_index))
        X_train, X_val = features_train[train_index], features_train[val_index]
        y_train, y_val = target_train[train_index], target_train[val_index]
        X_early_stop, y_early_stop = X_val, y_val
        if early_stopping_data != None:
            X_early_stop, y_early_stop = early_stopping_data
        (model, hist) = train_model(model_params, training_params, [(X_train, y_train), (X_early_stop, y_early_stop)])
        loss_train = model.evaluate(X_train, y_train, verbose=0)
        loss_val = model.evaluate(X_val, y_val, verbose=0)
        loss_test = model.evaluate(features_test, target_test, verbose=0)
        print("losses - train: %f, val: %f, test: %f" % (loss_train, loss_val, loss_test))
        losses.append({'train':loss_train, 'val':loss_val, 'test':loss_test})
        models.append(model)
        histories.append(hist)
        fold+=1
    return {'models': models, 'histories':histories, 'losses':losses, 'cv_indices':cv_indices}


def train_bs_models(model_params, training_params, data, n_samples=5, sample_size=None):
    [(features_train, target_train), (features_test, target_test)] = data
    train_indices_full = np.array(list(range(features_train.shape[0])))
    bs_size = sample_size
    if bs_size == None:
        bs_size = features_train.shape[0]
    models = []
    histories = []
    losses = []
    bs_indices = []
    for sample_index in range(n_samples):
        print('Sample %d ' % sample_index)
        train_index = np.random.choice(train_indices_full, size=bs_size, replace=True)
        X_train = features_train[train_index]
        y_train = target_train[train_index]
        (model, hist) = train_model(model_params, training_params, [(X_train, y_train), (features_test, target_test)])
        loss_train = model.evaluate(X_train, y_train, verbose=0)
        loss_test = model.evaluate(features_test, target_test, verbose=0)
        print("losses - train: %f, test: %f" % (loss_train, loss_test))
        losses.append({'train':loss_train, 'test':loss_test})
        bs_indices.append(train_index)
        models.append(model)
        histories.append(hist)
    return {'models': models, 'histories':histories, 'losses':losses, 'bs_indices':bs_indices}
