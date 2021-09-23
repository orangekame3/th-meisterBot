from slack_sdk.web import WebClient
from dynamodb_json import json_util as util
from boto3.session import Session
import matplotlib.pyplot as plt
import numpy as np
import boto3
import datetime
import pytz
import schedule
import time

def scan_table():
    response = dynamodb_table.scan()
    data = response['Items']
    return data

def marshall(regular_json):
    dynamodb_json = util.dumps(reular_json)
    return dynamodb_json

def unmarshall(dynamodb_json):
    regular_json = util.loads(dynamodb_json)
    return regular_json


def worker():

    data = scan_table()
    json_data = unmarshall(data)
    Humidity = []
    Temperature = []
    Timestamp = []
    Fukai = []
    for i in range(len(json_data)):
        temp = json_data[i]['temperature']
        humid = json_data[i]['humidity']
        times = json_data[i]['timestamp'][5:16]
        fukai = []
        if temp<25: 
            fukai.append("温度が低すぎます。")
        if temp>28:
            fukai.append("温度が高すぎます。")
        if humid<40:
            fukai.append("湿度が低すぎます。")
        if humid>70:
            fukai.append("湿度が高すぎます。")
        fukaisisuu = np.round(0.81*temp+0.01*humid*(0.99*temp-14.3)+46.3,2)
        fukai.append("不快指数は"+str(fukaisisuu)+"です。")
        Humidity.append(humid)
        Temperature.append(temp)
        Timestamp.append(times)
        Fukai.append(fukai)

    if len(Temperature)>15:
        Temperature = Temperature[len(Temperature)-15:]
        Humidity = Humidity[len(Humidity)-15:]
        Timestamp = Timestamp[len(Timestamp)-15:]
        Fukai = Fukai[len(Fukai)-15:]
        

    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['mathtext.fontset'] = 'stix'
    plt.rcParams["font.size"] = 20
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['figure.figsize'] = (8, 6)

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ln1=ax1.plot(Timestamp[:], Temperature[:], marker='o', markeredgewidth=1., markeredgecolor='k', color="orange",label=r'$Temperature$')
    ax2 = ax1.twinx()
    ln2=ax2.plot(Timestamp[:],Humidity[:], marker='o', markeredgewidth=1., markeredgecolor='k', color="blue",label=r'$Humidity$')
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1+h2, l1+l2, loc='upper right')
    ax1.set_ylim([20,32])
    ax2.set_ylim([25,85])
    ax1.axhspan(25, 28, color = "olive", alpha = 0.3)
    ax2.axhspan(40, 70, color = "royalblue", alpha = 0.2)    
    ax1.set_xlabel(r'$Timestamp$')
    ax1.set_ylabel(r'$Temperature$')
    ax2.set_ylabel(r'$Humidity$')
    ax1.grid(True)
    plt.gcf().autofmt_xdate() 
    plt.savefig("室内温湿度.jpg")

    client = WebClient(token="xoxb-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    response = client.chat_postMessage(text=" Temp : "+str(Temperature[-1])+"℃, Humid : "+str(Humidity[-1])+"%, message : "+"".join(Fukai[-1]), channel="#home")
    response = client.files_upload(channels="#home",file ="./室内温湿度.jpg",title="室内温湿度")
    now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
    print("Executed:", now.strftime('%Y-%m-%d %H:%M:%S'))

if __name__ == "__main__":
    session = Session(profile_name='default', region_name='ap-northeast-1')
    dynamodb = session.resource('dynamodb')
    dynamodb_table = dynamodb.Table('mydht22')
    schedule.every(2).hours.do(worker)
    while True:
        schedule.run_pending()
        time.sleep(1)
