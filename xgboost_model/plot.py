import chart_studio.plotly as py
import csv
import os
import pandas as pd
import plotly.graph_objs as go
import yaml

from collections import defaultdict
from datetime import date, timedelta

def gen_plotly_url():
    # Sign in to plotly if you haven't done so
    py.sign_in('ngyibin', '<YOUR-PASSWORD>')  # Be careful with this, don't put it on Github!!!

    # Get current working directory
    cwd = os.getcwd()

    # Load config
    with open(cwd+"/config/config.yml", 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # Load test file
    df = pd.read_csv(cwd+config['data_processed_path'], sep=",")

    # Load the predictions
    est_dict = {'date': [df[-1:]['date'].values[0]],
                'forecast': [df[-1:]['adj_close'].values[0]]}
    day = 1
    with open(cwd+'/out/est_' + str(date.today()) + '.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            est_dict['date'].append(str(date.today() + timedelta(days=day)))
            est_dict['forecast'].append(float(row[0]))
            day = day + 1
    est_df = pd.DataFrame(est_dict)

    # Plot with plotly
    miny = min(min(df[-63:]['adj_close']), min(est_df['forecast']))-1 # min y-value of the plot
    maxy = max(max(df[-63:]['adj_close']), max(est_df['forecast']))+1 # max y-value of the plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[-63:]['date'],
                             y=df[-63:]['adj_close'],
                             mode='lines',
                             name='actual',
                             line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=est_df['date'],
                             y=est_df['forecast'],
                             mode='lines',
                             name='predictions',
                             line=dict(color='red')))
    fig.add_trace(go.Scatter(x=[str(date.today()), str(date.today())],
                             y=[miny, maxy],
                             mode='lines',
                             line=dict(color='black', dash="dot"),
                             showlegend=False))
    fig.update_layout(yaxis=dict(title='USD'),
                      xaxis=dict(title='date'))
    fig.update_yaxes(range=[miny, maxy])
    
    url=py.plot(fig, filename='est_'+str(date.today()), auto_open=False)
    
    return url
