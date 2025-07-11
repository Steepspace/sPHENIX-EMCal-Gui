#!/usr/bin/env python3
import argparse
import telnetlib
import threading
import tkinter as tk
import numpy as np
import os
import time
import subprocess
import psycopg2
import pandas as pd
import pandas.io.sql as sqlio

# Author: Apurva Narde, UIUC
parser = argparse.ArgumentParser(description='GUI to monitor the voltages from the EMCal.')

parser.add_argument('-d', '--delay', type=int, default=30, help='Refresh time. Default: 30 seconds.')
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose.')
parser.add_argument('-b', '--dbname', type=str, default='daq', help='Database name. Default: daq')
parser.add_argument('-u', '--user', type=str, default='phnxro', help='User. Default: phnxro')
parser.add_argument('-s', '--host', type=str, default='db1.sphenix.bnl.gov', help='Database host. Default: db1.sphenix.bnl.gov')
parser.add_argument('-t', '--threshold', type=float, default=1, help='Maximum vmeas (measured voltage) when bias is OFF. Default: 1 V')

args = parser.parse_args()

verbose   = args.verbose
dbhost    = args.host
dbname    = args.dbname
user      = args.user
threshold = args.threshold

def get_bias_status():
    df = pd.DataFrame()
    try:
        with psycopg2.connect(f"host='{dbhost}' dbname='{dbname}' user='{user}'") as conn:
            sql = f'''SELECT
                        -vmeas as vmeas
                    FROM
                    emcal_mpodlog
                    WHERE readtime > (CURRENT_TIMESTAMP-INTERVAL '00:02:00')
                    and not ((sector = 50 and ib = 1) or (sector = 4 and ib = 1) or (sector = 25 and ib = 2) or (sector = 54 and ib = 4) or (sector = 10 and ib = 3) or (sector = 10 and ib = 5) or (sector = 60 and ib = 4))
                    ORDER BY readtime desc, sector, ib'''

            df = pd.read_sql_query(sql, conn)
    except:
        print(f'Failed to connect to {dbhost}, {dbname}')

    return df

def get_lv_status():
    df = pd.DataFrame()
    try:
        with psycopg2.connect(f"host='{dbhost}' dbname='{dbname}' user='{user}'") as conn:
            sql = '''SELECT
                        vp,
                        vn
                    FROM
                    emcal_iface
                    WHERE readtime > (CURRENT_TIMESTAMP-INTERVAL '00:02:00')
                    and not ((sector = 50 and ib = 1) or (sector = 4 and ib = 1) or (sector = 25 and ib = 2) or (sector = 54 and ib = 4) or (sector = 10 and ib = 3) or (sector = 10 and ib = 5) or (sector = 60 and ib = 4))
                    ORDER BY readtime desc, sector, ib'''

            df = pd.read_sql_query(sql, conn)

    except:
        print(f'Failed to connect to {dbhost}, {dbname}')

    return df

def update_status(bias_label, lv_label, delay):
    while(1):
        # update bias status
        df_bias = get_bias_status()

        if(df_bias.empty):
                bias_label.config(text='Bias Voltage \n No DB Connection \n Check Bias GUI', foreground='white', background='blue')
        else:
            off_counts = (df_bias['vmeas'].abs() < threshold).sum()
            total      = df_bias.index.size

            # no ib is under the threshold for being off
            if(off_counts == 0):
                bias_label.config(text='Bias Voltage is ON', background='green')

            # a fraction of the number of ibs are in the threshold for being off
            elif(off_counts < total):
                bias_label.config(text=f'Bias Voltage \n {off_counts}/{total} OFF \n Check Bias GUI', background='red')

            else:
                bias_label.config(text='Bias Voltage is OFF', background='grey')

        # update lv status
        df_lv = get_lv_status()

        if(df_lv.empty):
            lv_label.config(text='Low Voltage \n No DB Connection \n Check Low Voltage GUI', foreground='white', background='blue')
        else:
            off_counts = ((df_lv['vp'] < 5) | (df_lv['vp'] >= 7) | (df_lv['vn'] < -7) | (df_lv['vn'] >= -5)).sum()
            total      = df_lv.index.size

            # no ib is under the threshold for being off
            if(off_counts == 0):
                lv_label.config(text='Low Voltage is ON', background='green')

            # a fraction of the number of ibs are in the threshold for being off
            elif(off_counts < total):
                lv_label.config(text=f'Low Voltage \n {off_counts}/{total} OFF \n Check Low Voltage GUI', background='red')

            else:
                lv_label.config(text='Low Voltage is OFF', background='grey')

        threading.Event().wait(delay)

# call script to turn all voltage ON
def all_voltage_on():
    os.system('ssh phnxrc@opc0 "bash /home/phnxrc/haggerty/emcal/offandon/emcalon"')

# call script to turn all voltage OFF
def all_voltage_off():
    os.system('ssh phnxrc@opc0 "bash /home/phnxrc/haggerty/emcal/offandon/emcaloff"')

if __name__ == '__main__':
    delay     = args.delay
    font_size = 36

    root = tk.Tk()
    root.title('sPHENIX EMCal Voltage Monitor')
    root.geometry("1000x500")

    for i in range(2):
        tk.Grid.rowconfigure(root,i,weight=1)
        tk.Grid.columnconfigure(root,i,weight=1)

    # Create Labels
    label_1 = tk.Label(root,text="Bias Voltage is ON", font=('Times', font_size))
    label_2 = tk.Label(root,text="Low Voltage is ON", font=('Times', font_size))

    # Create Buttons
    button_1 = tk.Button(root,text="Turn on EMCal", font=('Times', font_size), command=lambda: all_voltage_on())
    button_2 = tk.Button(root,text="Turn off EMCal", font=('Times', font_size), command=lambda: all_voltage_off())

    # Set grid
    label_1.grid(row=0,column=0,sticky="NSEW")
    label_2.grid(row=0,column=1,sticky="NSEW")

    button_1.grid(row=1,column=0,sticky="NSEW")
    button_2.grid(row=1,column=1,sticky="NSEW")

    # create a separate thread which will execute the update_status at the given delay
    thread = threading.Thread(target=update_status, args=(label_1, label_2, delay))
    thread.start()

    root.mainloop()
