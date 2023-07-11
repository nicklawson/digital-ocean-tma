from flask import Flask, Response, request, jsonify
from flask_httpauth import HTTPBasicAuth
import os
import pandas as pd
import numpy as np
import pandas_ta as ta

app = Flask(__name__)
auth = HTTPBasicAuth()

# Define your users here. In a real application, this would probably come from a database.
users = {
    "niklas": "password1",
    "sarah": "password2"
}

allowed_ips = ["127.0.0.1", "193.183.240.84"]  # Add more IPs as needed

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

def calculate_tma(json,HalfLength=100,BandsDeviations=3,price_calculation='weighted'):

    df = pd.read_json(json)
    df = df.copy()

    if price_calculation == 'weighted':
        df.loc[:, 'Weighted_Price'] = (df['high'] + df['low'] + df['close'] + df['open']) / 4
        # df['Weighted_Price'] = (df['high'] + df['low'] + df['close'] + df['close']) / 4

    df['diff'] = np.nan  # initialize the wdBuffer column
    # df['wdBuffer'] = 0  # initialize the wdBuffer column
    # df['wuBuffer'] = 0  # initialize the wuBuffer column
    # df['upBuffer'] = 0  # initialize the wuBuffer column
    # df['dnBuffer'] = 0  # initialize the wuBuffer column

    df.loc[:, 'wdBuffer'] = 0
    df.loc[:, 'wuBuffer'] = 0
    df.loc[:, 'upBuffer'] = 0
    df.loc[:, 'dnBuffer'] = 0

    FullLength = 2 * HalfLength + 1
    # Reset the index of df
    df = df.reset_index(drop=True)

    # 01:41:00
    len_df = len(df)
    wp_values = df['Weighted_Price'].values

    for i in range(len_df):
        sum_price = (HalfLength + 1) * wp_values[i]
        sumw = (HalfLength + 1)
        k = HalfLength

        for j in range(1, HalfLength + 1):
            if i + j < len_df:
                sum_price += k * wp_values[i + j]
                sumw += k

            if j <= i:
                sum_price += k * wp_values[i - j]
                sumw += k

            k -= 1

        df.loc[i, 'tmac'] = sum_price / sumw

    # df['diff'] = df['SMA'] - df['tmac']

    df['diff'] = ta.sma(df["Weighted_Price"], length=1) - df['tmac']

    for i in range(len(df)):
        if i == HalfLength:
            if df.loc[i, 'diff'] >= 0:
                df.loc[i, 'wuBuffer'] = pow(df.loc[i, 'diff'],2)
                df.loc[i, 'wdBuffer'] = 0
            else:
                df.loc[i, 'wdBuffer'] = pow(df.loc[i, 'diff'],2)
                df.loc[i, 'wuBuffer'] = 0
        
        else:
            if df.loc[i, 'diff'] >= 0:
                try:
                    df.loc[i, 'wuBuffer'] = (df.loc[i-1, 'wuBuffer']*(FullLength-1)+pow(df.loc[i, 'diff'],2))/FullLength
                except:
                    df.loc[i, 'wuBuffer'] = pow(df.loc[i, 'wuBuffer'], 2)

                try:
                    df.loc[i, 'wdBuffer'] = df.loc[i-1, 'wdBuffer'] * (FullLength-1)/FullLength
                except:
                    df.loc[i, 'wdBuffer'] = df.loc[i, 'wdBuffer'] * (FullLength-1)/FullLength

            else:
                try:
                    df.loc[i, 'wdBuffer'] = (df.loc[i-1, 'wdBuffer']*(FullLength-1)+pow(df.loc[i, 'diff'],2))/FullLength
                except:
                    df.loc[i, 'wdBuffer'] = pow(df.loc[i, 'wdBuffer'], 2)

                try:
                    df.loc[i, 'wuBuffer'] = df.loc[i-1, 'wuBuffer'] * (FullLength-1)/FullLength
                except:
                    df.loc[i, 'wuBuffer'] = df.loc[i, 'wuBuffer'] * (FullLength-1)/FullLength

            df.loc[i, 'upBuffer'] = df.loc[i, 'tmac'] + BandsDeviations * np.sqrt(df.loc[i, 'wuBuffer'])
            df.loc[i, 'dnBuffer'] = df.loc[i, 'tmac'] - BandsDeviations * np.sqrt(df.loc[i, 'wdBuffer'])
            

    # upBuffer[i] = tmBuffer[i] + BandsDeviations*MathSqrt(wuBuffer[i]);
    # df['upBuffer'] = df['tmac'] + BandsDeviations * np.sqrt(df['wuBuffer'])
    # df['dnBuffer'] = df['tmac'] - BandsDeviations * np.sqrt(df['wdBuffer'])
    # print(df)
    
    return df

@app.route('/')
def home():
    return Response('Hello? Yes, this is dog!', status=200)

@app.route('/api', methods=['POST'])
@auth.login_required
def api():

    user_ip = request.remote_addr  # Get user IP
    if user_ip not in allowed_ips:
        print("Unauthorized IP: %s" % user_ip)
        return jsonify({"message": "Unauthorized IP"}), 401
    
    rates_json = request.json

    df = calculate_tma(rates_json)
    # Convert the dataframe to a json object
    content = df.to_json(orient='records')
    # Do something with the json content
    # For demonstration purposes, let's just send it back as the response
    return jsonify(content)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 80))
    print('Listening on port %s' % (port))
    app.run(host='0.0.0.0', port=port)