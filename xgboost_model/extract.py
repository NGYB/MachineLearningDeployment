import csv
import os
import requests
import yaml

from bs4 import BeautifulSoup
from datetime import date
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Get current working directory
cwd = os.getcwd()

with open(cwd+"/config/config.yml", 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

def parse(stock_code):
    """
    Parse yahoo finance webpage
    :return:
    stock year low, stock year high, stock price
    """
    url = "https://finance.yahoo.com/quote/%s" % (stock_code)
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.text, "lxml")

    # Find current price
    y = soup.findAll('span', attrs={'class': 'Trsdu(0.3s) Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(b)', 'data-reactid': "14"})[0]

    return float(y.text.replace(',', ''))

def insert(path, date, price):
    """
    Insert new data into the data file specified by path
    """
    with open(path, 'a') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow([str(date.today()), str(price)])
    
# Get latest price
price = parse(config['stock_code'])

# Insert into data file
insert(cwd+config['data_processed_path'], date, price)
