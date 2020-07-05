
import model as mod
import os
import pandas as pd
import yaml

from datetime import date
from numpy import savetxt

# Get current working directory
cwd = os.getcwd()

# Load config
with open(cwd+"/config/config.yml", 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# Load test file
data = pd.read_csv(cwd+config['data_processed_path'], sep=",")

# Create an instance of xgboost_model
xgb_model = mod.Xgboost_model(N=10, H=21)

# Do transformation
data = xgb_model.transform(data)

# Do prediction
est = xgb_model.predict(data)

# Save predictions to file
savetxt(cwd+'/out/est_' + str(date.today()) + '.csv', est, delimiter=',')
