#!/usr/bin/env python3
"""
Author: Apurva Narde, UIUC
EMCal Bias Voltage GUI
"""
import ast
import argparse
import threading
import tkinter as tk
from tkinter import ttk
import os
import subprocess
import re
import hvcontrol

parser = argparse.ArgumentParser(description='GUI to monitor the bias voltages from the EMCal.')

parser.add_argument('-d', '--delay', type=int, default=60, help='Refresh time. Default: 60 seconds.')
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose.')

args = parser.parse_args()

chnlist = {
        0: [
            "CH-0", "CH-1", "CH-2", "CH-3", "CH-4", "CH-5", "CH-6", "CH-7",
            "CH-8", "CH-9", "CH-10", "CH-11", "CH-12", "CH-13", "CH-14", "CH-15",
            "CH-16", "CH-17", "CH-18", "CH-19", "CH-20", "CH-21", "CH-22", "CH-23",
            "CH-24", "CH-25", "CH-26", "CH-27", "CH-28", "CH-29", "CH-30", "CH-31",
            "CH-32", "CH-33", "CH-34", "CH-35", "CH-36", "CH-37", "CH-38", "CH-39",
            "CH-40", "CH-41", "CH-42", "CH-43", "CH-44", "CH-45", "CH-46", "CH-47",
            "CH-48", "CH-49", "CH-50", "CH-51", "CH-52", "CH-53", "CH-54", "CH-55",
            "CH-56", "CH-57", "CH-58", "CH-59", "CH-60", "CH-61", "CH-62", "CH-63",
            "CH-64", "CH-65", "CH-66", "CH-67", "CH-68", "CH-69", "CH-70", "CH-71",
            "CH-72", "CH-73", "CH-74", "CH-75", "CH-76", "CH-77", "CH-78", "CH-79"
            ],
        1: [
            "CH-0", "CH-1", "CH-2", "CH-3", "CH-4", "CH-5", "CH-6", "CH-7",
            "CH-8", "CH-9", "CH-10", "CH-11", "CH-12", "CH-13", "CH-14", "CH-15"
        ]
}

mpod_ip={
    "3A2-1": 141,
    "3A2-2": 140,
    "3A5-1": 143,
    "3A5-2": 142,
    "3C2-1": 145,
    "3C2-2": 144,
    "3C8-1": 147,
    "3C8-2": 146
}

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

def emcalcon_voltage_one_crate(ip):
    """
    Get the EMCal Bias Voltage given an ip of crate.
    """
    prefix='/home/phnxrc/haggerty/snmp/bin/'
    #connect to the snmp crate
    getter = [prefix+'snmpwalk',
        '-OqU',
        '-v',
        '2c',
        '-M',
        '+/home/phnxrc/haggerty/MIBS',
        '-m',
        '+WIENER-CRATE-MIB',
        '-c',
        'public',
        ip,
        'outputMeasurementSenseVoltage']
    getter[-2] = ip
    answer = subprocess.run(getter, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    stateschan = answer.stdout.split('\n')[:-1]
    names=[]
    states=[]
    for i, statechan in enumerate(stateschan):
        name=statechan.split(" ")[0].split('.')[1]
        names.append(int(re.sub(r'\D', '',name)))
        states.append(statechan.split(" ")[1])
    startmodule=names[0]
    if startmodule==100:
        for i, name in enumerate(names):
            names[i] = name-100
            if names[i] >= 200:
                names[i] = names[i]-100
    #this is accounting for the one crate that has modules 100 and 300 but no 0 or 200
    for i, name in enumerate(names):
        names[i]= channel_index(name)
    sip= ip.split('.')[-1]
    sip = int(sip)%2
    chan = chnlist[sip]
    result = {chan[names[i]]: ast.literal_eval(states[i]) for i in range(len(states))}
    return result

def remap_bias(mpodbias):
    """
    Remap the bias from the mpod to sector, ib with correct sign.
    """
    bias={}
    for i in range(64):
        bias[i]={}
    for i in mpodbias:
        for j in mpodbias[i]:
            sector,ib=ib_map(i,j)
            bias[sector][ib]=-1*mpodbias[i][j] # this is to get the sign correct
    return bias

def ib_map(ip, channel_j):
    """
    Get the sector and ib given an ip address and channel index.
    """
    res=[ int(i) for i in channel_j.split("-") if i.isnumeric() ]
    channel=res[0]
    res1=[ int(i) for i in ip.split(".") if i.isnumeric() ]
    crateip=res1[-1]
    crate=""
    for i, mpod_ip_val in mpod_ip.items():
        if mpod_ip_val == crateip:
            crate=i
            slot=int(channel/8)
            channel=channel%8
    if crateip == 143 and slot == 0:
        slot = 3
    sector, ib = hvcontrol.mpod_channel_to_sector(crate, slot, channel)
    return sector, ib

def channel_name(channel_j):
    """
    Get channel name given a channel index.
    """
    res=[ int(i) for i in channel_j.split("-") if i.isnumeric() ]
    channel=res[0]
    slot=channel/8
    mod=channel%8
    cn=slot*100+mod
    channel_name_val="u"+str(cn)
    return channel_name_val

def channel_index(mod_ch_num):
    """
    Map the mod channel number to channel index.
    """
    module=int(mod_ch_num)/100
    module=int(module)
    channel=(int(mod_ch_num) % 100 ) % 8
    index=channel+8*module
    #print(str(mod_ch_num)+" index: " + str(index))
    return index

def update_status(ib_status, delay, busy, verbose, nSectors=64, nIBs=6):
    """
    Automatically update the status of the bias voltages on GUI at regular intervals.
    """
    while True:
        if not busy[0]:
            busy[0] = True

            biasmpod={}
            bias={}

            for _, mpod_ip_val in mpod_ip.items():
                ip="10.20.34."+str(mpod_ip_val)
                biasmpod[ip]=emcalcon_voltage_one_crate(ip)
            bias=remap_bias(biasmpod)

            for sector in range(nSectors):
                for ib in range(nIBs):
                    ib_status[sector][ib].config(background='black')

            for sector in range(nSectors):

                if not bias[sector]:
                    print(f'No bias voltage found for S: {sector}')
                    continue
                    # ib_status[sector][ib].config(background='black')

                # plot bias
                for ib in range(nIBs):
                    if verbose:
                        ib_status[sector][ib].config(text=f'ib {ib}: {bias[sector][ib]:06.2f} V')
                    else:
                        ib_status[sector][ib].config(text=f'ib {ib}')

                    if ib not in bias[sector]:
                        print(f'No bias voltage found for S: {sector}, IB: {ib}')
                        continue

                    if bias[sector][ib] >= -5:
                        ib_status[sector][ib].config(background='red')
                    elif bias[sector][ib] >= -64:
                        ib_status[sector][ib].config(background='orange')
                    elif bias[sector][ib] >= -68:
                        ib_status[sector][ib].config(background='green')
                    else:
                        ib_status[sector][ib].config(background='purple')

            # known bad ib boards
            ib_status[50][1].config(background='gray')
            ib_status[4][1].config(background='gray')
            ib_status[25][2].config(background='gray')
            # Additional bad ib boards in Run 25
            ib_status[54][4].config(background='gray')
            ib_status[10][3].config(background='gray')
            busy[0] = False
        else:
            print('Currently busy')
        threading.Event().wait(delay)

def bias_voltage_on():
    """
    call script to turn bias voltage ON
    """
    # testing
    # subprocess.call('./template/on.sh')
    os.system('ssh phnxrc@opc0 "bash /home/phnxrc/BiasControl/onemall.sh"')

def bias_voltage_off():
    """
    call script to turn bias voltage OFF
    """
    # testing
    # subprocess.call('./template/off.sh')
    os.system('ssh phnxrc@opc0 "bash /home/sphenix-slow/BiasControl/offemall.sh"')

def initGui():
    """
    Initialize the default state of GUI and kicks of the thread to run the GUI asynchronously.
    """
    delay   = args.delay
    verbose = args.verbose
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
        sector_title.config(background='green3')
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
    legend_map = {'< -68 V'              :'purple',
                  '-68 V to -64 V'       :'green',
                  '-64 V to -5 V'        :'orange',
                  '>= -5 V'              :'red',
                  'Known Bad'            :'gray'}

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

    # keeps track of whether telnet is being used
    busy = [False]

    for i in range(2):
        temp = ttk.Label(legend, text='', background='white')
        temp.grid(row=len(legend_map)+i+5, column=0, columnspan=2, sticky='NS')

    bias_legend_title = ttk.Label(legend, text='Bias Voltage', background='white')
    bias_legend_title.grid(row=len(legend_map)+7, column=0, columnspan=2, sticky='NS')

    # create button to turn ON bias voltage
    button2 = ttk.Button(legend, text='Bias Voltage ON', command=bias_voltage_on())
    button2.grid(row=len(legend_map)+8, column=0, columnspan=2, sticky='EW')

    # create button to turn OFF bias voltage
    button3 = ttk.Button(legend, text='Bias Voltage OFF', command=bias_voltage_off())
    button3.grid(row=len(legend_map)+9, column=0, columnspan=2, sticky='EW')

    # create a separate thread which will execute the update_status at the given delay
    thread = threading.Thread(target=update_status, args=(ib_status, delay, busy, verbose))
    thread.start()

    root.mainloop()

if __name__ == '__main__':
    initGui()
