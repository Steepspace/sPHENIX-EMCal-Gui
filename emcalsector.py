#!/usr/bin/env python3
import argparse
import telnetlib
import threading
import tkinter as tk
from tkinter import ttk
import numpy as np
import subprocess

# Author: Apurva Narde, UIUC

parser = argparse.ArgumentParser(description='GUI to monitor the bias voltages from the EMCal.')

parser.add_argument('-d', '--delay', type=int, default=60, help='Refresh time. Default: 60 seconds.')
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose.')

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

def emcalcon_gain(tn):
    tn.write(b'\n\r')
    tn.write(b'\n\r')
    nib=6
    gains = []
    for ib in range(0, nib):
        command='$A'+str(ib)
        tn.write(command.encode('ascii')+b'\n\r')
        x = tn.read_until(b'>')
        gainstring = x.decode('ascii')
        # print(gainstring)
        y = gainstring.split('=')
        # print(y)
        z = y[1].strip('\n\r>')
        gains.append(z)
    # print(gains)
    return gains

def emcalcon_setgain(tn, whichgain):
    tn.write(b'\n\r')
    tn.write(b'\n\r')

    nib = 6

    if whichgain == 'high':
        for ib in range(0,nib):
            command = '$A'+str(ib)+'h'
            tn.write(command.encode('ascii'))
            g = tn.read_until(b'>')
            print(g.decode('ascii'))
            tn.write(b'\n\r')
#here is the checking loop, if this fails take it out
#           time.sleep(1)
            command = '$A'+str(ib)
            tn.write(command.encode('ascii'))
            g = tn.read_until(b'>')
            status=str(g.decode('ascii'))
            tn.write(b'\n\r')
            while "igh" not in status:

                command = '$A'+str(ib)+'h'
                tn.write(command.encode('ascii'))
                g = tn.read_until(b'>')
                tn.write(b'\n\r')

                command = '$A'+str(ib)
                tn.write(command.encode('ascii'))
                g = tn.read_until(b'>')
                status=str(g.decode('ascii'))
                tn.write(b'\n\r')
            print('EMCAL high gain enabled')

    else:
        for ib in range(0,nib):
            command = '$A'+str(ib)+'n'
            tn.write(command.encode('ascii'))
            g = tn.read_until(b'>')
            print(g.decode('ascii'))
            tn.write(b'\n\r')
            #time.sleep(1)
            command = '$A'+str(ib)
            tn.write(command.encode('ascii'))
            g = tn.read_until(b'>')
            status=str(g.decode('ascii'))
            tn.write(b'\n\r')
            while "Norm" not in status:

                command = '$A'+str(ib)+'h'
                tn.write(command.encode('ascii'))
                g = tn.read_until(b'>')
                tn.write(b'\n\r')

                command = '$A'+str(ib)
                tn.write(command.encode('ascii'))
                g = tn.read_until(b'>')
                status=str(g.decode('ascii'))
                tn.write(b'\n\r')

        print('EMCAL gain set to normal (low)')

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

    # get gain modes
    gain = emcalcon_gain(tn)

    # close connection
    emcalcon_disconnect(tn)

    return bias, gain

def update_status(sector_status, ib_status, delay, verbose, busy, gains, nSectors=64, nIBs=6):
    while True:
        if(not busy[0]):
            busy[0] = True
            # get status
            for sector in range(nSectors):
                for ib in range(nIBs):
                    ib_status[sector][ib].config(background='black')

            for sector in range(nSectors):
                try:
                    bias, gain = get_status(sector)

                    # testing
                    # bias = np.random.choice([-70,-65,-10,0], nIBs, True, [0.01,0.95,0.02,0.02])
                    # gain = np.random.choice(['Norm','High'], nIBs, True, [0.99,0.01])
                except Exception as ex:
                    bias = [None]*nIBs
                    print(f'Error in retrieving bias for sector: {sector}')

                if('High' in gain):
                    sector_status[sector].config(background='brown')
                    gains[sector] = 'High'
                else:
                    sector_status[sector].config(background='green3')
                    gains[sector] = 'Norm'

                for ib in range(nIBs):
                    if(verbose):
                        ib_status[sector][ib].config(text=f'ib {ib}: {bias[ib]:06.2f} V')
                    else:
                        ib_status[sector][ib].config(text=f'ib {ib}')

                    if(bias[ib] is None):
                        ib_status[sector][ib].config(background='black')
                    elif(bias[ib] >= -5):
                        ib_status[sector][ib].config(background='red')
                    elif(bias[ib] >= -64):
                        ib_status[sector][ib].config(background='orange')
                    elif(bias[ib] >= -68):
                        ib_status[sector][ib].config(background='green')
                    else:
                        ib_status[sector][ib].config(background='purple')

            # known bad ib boards
            ib_status[50][1].config(background='gray')

            busy[0] = False
        else:
            print('Currently busy')
        threading.Event().wait(delay)

def reset_gain(sector):
    # get connection
    host = all_controller_ip[sector]
    tn = emcalcon_connect(host)

    # set gain to normal
    emcalcon_setgain(tn,'normal')

    # close connection
    emcalcon_disconnect(tn)

def action(busy, gains, nSectors=64):
    if(not busy[0]):
        busy[0] = True
        for sector in range(nSectors):
            # testing
            # print(f'sector: {sector}, gain: {gains[sector]}')
            if(gains[sector] != 'Norm'):
                try:
                    reset_gain(sector)
                except Exception as ex:
                    print(f'Error in resetting gain for sector {sector}')

        busy[0] = False
    else:
        print('Currently busy, try again shortly.')

# call script to turn bias voltage ON
def bias_voltage_on():
    # testing
    # subprocess.call('./template/on.sh')
    subprocess.call('/home/phnxrc/BiasControl/onemall.sh')

# call script to turn bias voltage OFF
def bias_voltage_off():
    # testing
    # subprocess.call('./template/off.sh')
    subprocess.call('/home/phnxrc/BiasControl/offemall.sh')

if __name__ == '__main__':
    delay     = args.delay
    # threshold = args.threshold
    verbose   = args.verbose
    # Number of sectors in the EMCal
    nSectors  = 64
    # Number of interface boards (IB) in each sector
    nIBs      = 6

    root = tk.Tk()
    root.title('sPHENIX EMCal Bias Monitor')

    # create style
    s = ttk.Style()
    s.configure('mainFrame.TFrame',background='#3A3845')
    s.configure('legend.TFrame',background='white')
    s.configure('button.TFrame',background='gray')

    # make the window resizable
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    frame = ttk.Frame(root, width=1000, height=500, style='mainFrame.TFrame')
    frame.grid(row=0,column=0, sticky='NEWS')

    # initial the GUI layout
    ib_status = {}
    sector_status = []
    for i in range(nSectors):
        sector = ttk.Frame(frame, width=50, height=100)
        sector.grid(row=i//16, column=i%16, padx=2, pady=2, sticky='EW')
        sector_title = ttk.Label(sector, text=f'S {i}')
        sector_title.grid(row=0, column=0, sticky='EW')
        sector_status.append(sector_title)
        ib_arr = []
        for j in range(nIBs):
            ib = ttk.Label(sector, text=f'ib {j}')
            ib.grid(row=j+1, column=0, sticky='EW')
            ib_arr.append(ib)

        # make the window resizable
        sector.columnconfigure(0, weight=1)
        sector.rowconfigure(tuple(range(7)), weight=1)

        ib_status[i] = ib_arr

    # configure legend
    legend_map = {'< -68 V'       :'purple',
                  '-68 V to -64 V':'green',
                  '-64 V to -5 V' :'orange',
                  '>= -5 V'       :'red',
                  'Known Bad'     :'gray'}

    legend = ttk.Frame(frame, width=75, height=100, style='legend.TFrame')
    legend.grid(row=0, column=16, padx=2, pady=2, rowspan=6, sticky='NEWS')

    legend_title = ttk.Label(legend, text='IB Legend', background='white')
    legend_title.grid(row=0, column=0, columnspan=2)

    for index, item in enumerate(legend_map.items()):
        key, value = item
        legend_cell = ttk.Label(legend, background=value, width=3)
        legend_cell.grid(row=index+1, column=0, padx=5, pady=5, sticky='NEWS')

        legend_cell = ttk.Label(legend, text=key, background='white')
        legend_cell.grid(row=index+1, column=1, sticky='NS')


    blank_lines = 5
    for i in range(blank_lines):
        temp = ttk.Label(legend, text='', background='white')
        temp.grid(row=len(legend_map)+i+1, column=0, columnspan=2, sticky='NS')

    sector_legend_title = ttk.Label(legend, text='Sector Legend', background='white')
    sector_legend_title.grid(row=len(legend_map)+blank_lines, column=0, columnspan=2, sticky='NS')

    # configure legend
    sector_legend_map = {'Normal Gain'   :'green3',
                         'High Gain'     :'brown'}

    for index, item in enumerate(sector_legend_map.items()):
        key, value = item
        legend_cell = ttk.Label(legend, background=value, width=3)
        legend_cell.grid(row=len(legend_map)+index+blank_lines+1, column=0, padx=5, pady=5, sticky='NEWS')

        legend_cell = ttk.Label(legend, text=key, background='white')
        legend_cell.grid(row=len(legend_map)+index+blank_lines+1, column=1, sticky='NS')

    # keeps track of whether telnet is being used
    busy = [False]

    # initally have the gains status be all normal
    gains = ['Norm']*nSectors

    # create button to reset the gains
    button = ttk.Button(legend, text='Restore Normal Gain', command=lambda: action(busy, gains))
    button.grid(row=len(legend_map)+len(sector_legend_map)+blank_lines+1, column=0, columnspan=2)

    for i in range(2):
        temp = ttk.Label(legend, text='', background='white')
        temp.grid(row=len(legend_map)+blank_lines+i+5, column=0, columnspan=2, sticky='NS')

    bias_legend_title = ttk.Label(legend, text='Bias Voltage', background='white')
    bias_legend_title.grid(row=len(legend_map)+blank_lines+7, column=0, columnspan=2, sticky='NS')

    # create button to turn ON bias voltage
    button2 = ttk.Button(legend, text='Bias Voltage ON', command=lambda: bias_voltage_on())
    button2.grid(row=len(legend_map)+len(sector_legend_map)+blank_lines+8, column=0, columnspan=2, sticky='EW')

    # create button to turn ON bias voltage
    button3 = ttk.Button(legend, text='Bias Voltage OFF', command=lambda: bias_voltage_off())
    button3.grid(row=len(legend_map)+len(sector_legend_map)+blank_lines+9, column=0, columnspan=2, sticky='EW')

    # make the window resizable
    frame.columnconfigure(tuple(range(17)), weight=1)
    frame.rowconfigure(tuple(range(4)), weight=1)

    # create a separate thread which will execute the update_status at the given delay
    thread = threading.Thread(target=update_status, args=(sector_status, ib_status, delay, verbose, busy, gains))
    thread.start()

    root.mainloop()
