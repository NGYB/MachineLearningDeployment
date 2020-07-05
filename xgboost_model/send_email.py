
import csv
import os
import pandas as pd
import plot as pl
import smtplib
import email.utils
import yaml
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Get current working directory
cwd = os.getcwd()

# Load config
with open(cwd+"/config/config.yml", 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# Replace sender@example.com with your "From" address.
# This address must be verified.
SENDER = '<YOUR-EMAIL-ADDRESS>'
SENDERNAME = '<YOUR-COMPANYS-NAME>'

# Replace recipient@example.com with a "To" address. If your account
# is still in the sandbox, this address must be verified.
RECIPIENT = ['<TO-EMAIL-ADDRESS1>']

# Replace smtp_username with your Amazon SES SMTP user name.
USERNAME_SMTP = "<YOUR-USERNAME>" # Be careful with this, don't put it on Github!!!

# Replace smtp_password with your Amazon SES SMTP password.
PASSWORD_SMTP = "<YOUR-PASSWORD>" # Be careful with this, don't put it on Github!!!

# If you're using Amazon SES in an AWS Region other than US West (Oregon),
# replace email-smtp.us-west-2.amazonaws.com with the Amazon SES SMTP
# endpoint in the appropriate region.
HOST = "email-smtp.us-west-2.amazonaws.com"
PORT = 587

# Load predictions into a list
est = []
with open(cwd+'/out/est_' + str(date.today()) + '.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        est.append(row[0])

# The subject line of the email.
SUBJECT = 'Results for ' + str(date.today())

# Load test file
data = pd.read_csv(cwd+config['data_processed_path'], sep=",")

# Run the plot script
url = pl.gen_plotly_url()

# The email body for recipients with non-HTML email clients.
BODY_TEXT = ("Current price: " + 
             str(data[-1:]['adj_close'].values) + 
             "\n Forecast for next 21 days using XGBoost: " +
             str(est))

# The HTML body of the email.
BODY_HTML = """<html>
<head>
<style>
table, th, td {{
  border: 1px solid black;
  border-collapse: collapse;
}}
th, td {{
  padding: 15px;
}}
</style>
</head>
<body>
  <h1>Current price</h1>
  <p>""" + "{0:.2f}".format(float(data[-1:]['adj_close'].values)) + """</p>
  <h1>Forecast for next 21 days using XGBoost</h1>
  <table>
    <tr><th>Day</th><th>Forecast</th></tr>
    <tr><td>1</td><td>""" + "{0:.2f}".format(float(est[0])) + """</td></tr>
    <tr><td>2</td><td>""" + "{0:.2f}".format(float(est[1])) + """</td></tr>
    <tr><td>3</td><td>""" + "{0:.2f}".format(float(est[2])) + """</td></tr>
    <tr><td>4</td><td>""" + "{0:.2f}".format(float(est[3])) + """</td></tr>
    <tr><td>5</td><td>""" + "{0:.2f}".format(float(est[4])) + """</td></tr>
    <tr><td>6</td><td>""" + "{0:.2f}".format(float(est[5])) + """</td></tr>
    <tr><td>7</td><td>""" + "{0:.2f}".format(float(est[6])) + """</td></tr>
    <tr><td>8</td><td>""" + "{0:.2f}".format(float(est[7])) + """</td></tr>
    <tr><td>9</td><td>""" + "{0:.2f}".format(float(est[8])) + """</td></tr>
    <tr><td>10</td><td>""" + "{0:.2f}".format(float(est[9])) + """</td></tr>
    <tr><td>11</td><td>""" + "{0:.2f}".format(float(est[10])) + """</td></tr>
    <tr><td>12</td><td>""" + "{0:.2f}".format(float(est[11])) + """</td></tr>
    <tr><td>13</td><td>""" +"{0:.2f}".format(float(est[12])) + """</td></tr>
    <tr><td>14</td><td>""" + "{0:.2f}".format(float(est[13])) + """</td></tr>
    <tr><td>15</td><td>""" + "{0:.2f}".format(float(est[14])) + """</td></tr>
    <tr><td>16</td><td>""" + "{0:.2f}".format(float(est[15])) + """</td></tr>
    <tr><td>17</td><td>""" + "{0:.2f}".format(float(est[16])) + """</td></tr>
    <tr><td>18</td><td>""" + "{0:.2f}".format(float(est[17])) + """</td></tr>
    <tr><td>19</td><td>""" + "{0:.2f}".format(float(est[18])) + """</td></tr>
    <tr><td>20</td><td>""" + "{0:.2f}".format(float(est[19])) + """</td></tr>
    <tr><td>21</td><td>""" + "{0:.2f}".format(float(est[20])) + """</td></tr>
  </table>
  <a href="{graph_url}" target="_blank">
    <img src="{graph_url}.png">
  </a>
  {caption}
  <br>
  <a href="{graph_url}" style="color: rgb(190,190,190); text-decoration: none; font-weight: 200;" target="_blank">
    Click to comment and see the interactive graph  
  </a>
  <br>
  <hr>  
</body>
</html>
"""
BODY_HTML = BODY_HTML.format(graph_url=url, caption='')

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = SUBJECT
msg['From'] = email.utils.formataddr((SENDERNAME, SENDER))
msg['To'] = ", ".join(RECIPIENT)
# Comment or delete the next line if you are not using a configuration set
#msg.add_header('X-SES-CONFIGURATION-SET',CONFIGURATION_SET)

# Record the MIME types of both parts - text/plain and text/html.
part1 = MIMEText(BODY_TEXT, 'plain')
part2 = MIMEText(BODY_HTML, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)
msg.attach(part2)

# Try to send the message.
try:
    server = smtplib.SMTP(HOST, PORT)
    server.ehlo()
    server.starttls()
    #stmplib docs recommend calling ehlo() before & after starttls()
    server.ehlo()
    server.login(USERNAME_SMTP, PASSWORD_SMTP)
    server.sendmail(SENDER, RECIPIENT, msg.as_string())
    server.close()
# Display an error message if something goes wrong.
except Exception as e:
    print ("Error: ", e)
else:
    print ("Email sent!")
