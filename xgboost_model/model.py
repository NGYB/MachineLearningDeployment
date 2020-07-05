
import joblib
import os
import pandas as pd
import numpy as np
import xgboost

from collections import defaultdict

# Get current working directory
cwd = os.getcwd()

class Xgboost_model:
    def __init__(self, N, H):
        """
        Initialize model.
        Inputs
            N: For feature at day t, we use lags from t-1, t-2, ..., t-N as features
            H: Forecast horizon, in days. Note there are about 252 trading days in a year
        """
        # Load model. This is what you get when you do joblib.dump(model, "weights.pkl")
        self.model = joblib.load(cwd+"/weights.pkl")

        # Load parameters
        self.N = N
        self.H = H

        # Get list of features
        self.features = []
        for n in range(self.N, 0, -1):
            self.features.append("adj_close_lag_"+str(n))

    def add_lags(self, df, N, lag_cols):
        """
        Add lags up to N number of days to use as features
        The lag columns are labelled as 'adj_close_lag_1', 'adj_close_lag_2', ... etc.
        """
        # Use lags up to N number of days to use as features
        df_w_lags = df.copy()
        # Add a column 'order_day' to indicate the order of the rows by date
        df_w_lags.loc[:, 'order_day'] = [x for x in list(range(len(df)))]
        merging_keys = ['order_day']  # merging_keys
        shift_range = [x+1 for x in range(N)]
        for shift in shift_range:
            train_shift = df_w_lags[merging_keys + lag_cols].copy()

            # E.g. order_day of 0 becomes 1, for shift = 1.
            # So when this is merged with order_day of 1 in df_w_lags, this will represent lag of 1.
            train_shift['order_day'] = train_shift['order_day'] + shift

            def foo(x): return '{}_lag_{}'.format(
                x, shift) if x in lag_cols else x
            train_shift = train_shift.rename(columns=foo)

            df_w_lags = pd.merge(df_w_lags, train_shift,
                                 on=merging_keys, how='left')  # .fillna(0)
        del train_shift

        return df_w_lags

    def do_scaling(self, df, N):
        """
        Do scaling for the adj_close and lag cols
        """
        df.loc[:, 'adj_close_scaled'] = (
            df['adj_close'] - df['adj_close_mean']) / df['adj_close_std']
        for n in range(N, 0, -1):
            df.loc[:, 'adj_close_scaled_lag_'+str(n)] = \
                (df['adj_close_lag_'+str(n)] - df['adj_close_mean']) / df['adj_close_std']

            # Remove adj_close_lag column which we don't need anymore
            df.drop(['adj_close_lag_'+str(n)], axis=1, inplace=True)

        return df

    def get_mov_avg_std(self, df, col, N):
        """
        Given a dataframe, get mean and std dev at timestep t using values from t-1, t-2, ..., t-N.
        Inputs
            df         : dataframe. Can be of any length.
            col        : name of the column you want to calculate mean and std dev
            N          : get mean and std dev at timestep t using values from t-1, t-2, ..., t-N
        Outputs
            df_out     : same as df but with additional column containing mean and std dev
        """
        mean_list = df[col].rolling(
            window=N, min_periods=1).mean()  # len(mean_list) = len(df)
        # first value will be NaN, because normalized by N-1
        std_list = df[col].rolling(window=N, min_periods=1).std()

        # Add one timestep to the predictions
        mean_list = np.concatenate(
            (np.array([np.nan]), np.array(mean_list[:-1])))
        std_list = np.concatenate(
            (np.array([np.nan]), np.array(std_list[:-1])))

        # Append mean_list to df
        df_out = df.copy()
        df_out[col + '_mean'] = mean_list
        df_out[col + '_std'] = std_list

        return df_out

    def transform(self, data):
        """
        Do transformation on data
        """
        data0 = data.copy(deep=True)
        
        # Add lags up to N number of days to use as features
        data0 = self.add_lags(data0, self.N, ['adj_close'])

        # Get mean and std dev at timestamp t using values from t-1, ..., t-N
        data0 = self.get_mov_avg_std(data0, 'adj_close', self.N)

        # Do scaling
        data0 = self.do_scaling(data0, self.N)
        
        # Drop the NaNs
        data0.dropna(axis=0, how='any', inplace=True)

        return data0

    def pred_xgboost(self, model, N, H, prev_vals, prev_mean_val, prev_std_val):
        """
        Do recursive forecasting using xgboost
        Inputs
            model              : the xgboost model
            N                  : for feature at day t, we use lags from t-1, t-2, ..., t-N as features
            H                  : forecast horizon
            prev_vals          : numpy array. If predict at time t, 
                                 prev_vals will contain the N unscaled values at t-1, t-2, ..., t-N
            prev_mean_val      : the mean of the unscaled values at t-1, t-2, ..., t-N
            prev_std_val       : the std deviation of the unscaled values at t-1, t-2, ..., t-N
        Outputs
            Times series of predictions. Numpy array of shape (H,). This is unscaled.
        """
        forecast = prev_vals.copy()

        for n in range(H):
            forecast_scaled = (forecast[-N:] - prev_mean_val) / prev_std_val

            # Create the features dataframe
            X = defaultdict(list)
            for n in range(N, 0, -1):
                X['adj_close_scaled_lag_'+str(n)] = [forecast_scaled[-n]]
            X = pd.DataFrame(X)

            # Do prediction
            est_scaled = self.model.predict(X)

            # Unscale the prediction
            forecast = np.concatenate([forecast,
                                       np.array((est_scaled * prev_std_val) + prev_mean_val).reshape(1,)])

            # Comp. new mean and std
            prev_mean_val = np.mean(forecast[-N:])
            prev_std_val = np.std(forecast[-N:])

        return forecast[-H:]

    def predict(self, df):
        """
        Do predictions
        """
        prev_vals = df[-self.N:]['adj_close'].to_numpy()
        prev_mean_val = np.mean(prev_vals)
        prev_std_val = np.std(prev_vals)

        # Get predicted labels and scale back to original range
        est = self.pred_xgboost(self.model, self.N, self.H, prev_vals,
                                prev_mean_val, prev_std_val)

        return est
