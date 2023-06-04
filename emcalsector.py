#!/usr/bin/env python3
import argparse
import telnetlib
import threading
import tkinter as tk
from tkinter import ttk

# Author: Apurva Narde, UIUC

parser = argparse.ArgumentParser(description='GUI to monitor the bias voltages from the EMCal.')

parser.add_argument('-d', '--delay', type=int, default=60, help='Refresh time. Default: 60 seconds.')
parser.add_argument('-t', '--threshold', type=float, default=5, help='Mark cell as red if absolute value of bias drops below threshold. Default: 5 V.')

args = parser.parse_args()

controller_ip = {
    # north
    '3C2':
    { 8: '10.20.34.42',
      9: '10.20.34.43',
      10: '10.20.34.44',
      11: '10.20.34.45',
      12: '10.20.34.46',
      13: '10.20.34.47',
      14: '10.20.34.48',
      15: '10.20.34.49',
      16: '10.20.34.50',
      17: '10.20.34.51',
      18: '10.20.34.52',
      19: '10.20.34.53',
      20: '10.20.34.54',
      21: '10.20.34.55',
      22: '10.20.34.56',
      23: '10.20.34.57' },
    '3C8':
    { 0: '10.20.34.65',
      1: '10.20.34.64',
      2: '10.20.34.63',
      3: '10.20.34.62',
      4: '10.20.34.61',
      5: '10.20.34.60',
      6: '10.20.34.59',
      7: '10.20.34.58',
      24: '10.20.34.73',
      25: '10.20.34.72',
      26: '10.20.34.71',
      27: '10.20.34.70',
      28: '10.20.34.69',
      29: '10.20.34.68',
      30: '10.20.34.67',
      31: '10.20.34.66' },
    # south
    '3A2':
    { 40: '10.20.34.10',
      41: '10.20.34.11',
      42: '10.20.34.12',
      43: '10.20.34.13',
      44: '10.20.34.14',
      45: '10.20.34.15',
      46: '10.20.34.16',
      47: '10.20.34.17',
      48: '10.20.34.18',
      49: '10.20.34.19',
      50: '10.20.34.20',
      51: '10.20.34.21',
      52: '10.20.34.22',
      53: '10.20.34.23',
      54: '10.20.34.24',
      55: '10.20.34.25' },
    '3A5':
    { 39: '10.20.34.26',
      38: '10.20.34.27',
      37: '10.20.34.28',
      36: '10.20.34.29',
      35: '10.20.34.30',
      34: '10.20.34.31',
      33: '10.20.34.32',
      32: '10.20.34.33',
      63: '10.20.34.34',
      62: '10.20.34.35',
      61: '10.20.34.36',
      60: '10.20.34.37',
      59: '10.20.34.38',
      58: '10.20.34.39',
      57: '10.20.34.40',
      56: '10.20.34.41' },
}

# it's convenient to have all the controller ip's by sector, too
all_controller_ip = {}
for r in controller_ip.keys():
    all_controller_ip = {**all_controller_ip, **controller_ip[r]}

def emcalcon_connect(HOST):
    PORT = '9760'
    try:
        tn = telnetlib.Telnet(HOST,PORT)
    except Exception as ex:
        print(ex)
        raise

    return tn

def emcalcon_disconnect(tn):
    tn.close()

def emcalcon_voltage(tn, ib):
    command = '$U'
    command += str(ib)
    tn.write(command.encode('ascii')+b"\n\r")
    x = tn.read_until(b">")
    line = x.decode('ascii')
    tn.write(b"\n\r")

    sline = line.rstrip()
    line = sline.lstrip()
    line = line.replace('\r', '')
    tstr = str(line)
    readback = tstr.split('\n')

    readback.remove('>')

    return float(readback[0].split('=')[3])

def get_status(sector):
    # number of ib boards in the sector
    nib = 6

    # get connection
    host = all_controller_ip[sector]
    tn = emcalcon_connect(host)

    # get bias values
    bias = []
    for ib in range(nib):
        bias.append(emcalcon_voltage(tn, ib))

    # close connection
    emcalcon_disconnect(tn)

    return bias

def update_status(ib_status, delay, threshold):
    while True:
        # get status
        for sector in range(64):
            for ib in range(6):
                ib_status[sector][ib].config(background='black')

        for sector in range(64):
            try:
                bias = get_status(sector)
            except Exception as ex:
                bias = [None]*6

            for ib in range(6):
                ib_status[sector][ib].config(text=f'ib {ib}: {bias[ib]:06.2f} V')
                ib_status[sector][ib].config(background='white')
                if(bias[ib] is None):
                    ib_status[sector][ib].config(background='black')
                elif(abs(bias[ib]) < threshold):
                    ib_status[sector][ib].config(background='red')
                else:
                    ib_status[sector][ib].config(background='green')

        threading.Event().wait(delay)

if __name__ == '__main__':
    delay     = args.delay
    threshold = args.threshold
    # Number of sectors in the EMCal
    nSectors  = 64
    # Number of interface boards (IB) in each sector
    nIBs      = 6

    root = tk.Tk()
    root.title('sPHENIX EMCal Bias Monitor')

    # create style
    s = ttk.Style()
    s.configure('mainFrame.TFrame',background='#3A3845')

    # make the window resizable
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    frame = ttk.Frame(root, width=1000, height=500, style='mainFrame.TFrame')
    frame.grid(row=0,column=0, sticky='NEWS')

    # initial the GUI layout
    ib_status = {}
    for i in range(nSectors):
        sector = ttk.Frame(frame, width=50, height=100)
        sector.grid(row=i//16,column=i%16, padx=5, pady=5, sticky='EW')
        sector_title = ttk.Label(sector, text=f'Sector {i}')
        sector_title.grid(row=0,column=0)
        ib_arr = []
        for j in range(nIBs):
            ib = ttk.Label(sector, text=f'ib {j}')
            ib.grid(row=j+1, column=0, sticky='EW')
            ib_arr.append(ib)

        # make the window resizable
        sector.columnconfigure(0, weight=1)
        sector.rowconfigure(tuple(range(7)), weight=1)

        ib_status[i] = ib_arr

    # make the window resizable
    frame.columnconfigure(tuple(range(16)), weight=1)
    frame.rowconfigure(tuple(range(4)), weight=1)

    # create a separate thread which will execute the update_status at the given delay
    thread = threading.Thread(target=update_status, args=(ib_status, delay, threshold))
    thread.start()

    root.mainloop()
