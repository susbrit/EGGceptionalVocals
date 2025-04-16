import csv
import openpyxl
import pprint
from pitch import proc_freq_data

# hardcoded wb file
wb = openpyxl.load_workbook('data/Izzy C Major Scale Mic Only.xlsx')
times, pitches = proc_freq_data(wb, 40)

filename = 'data/CQ Unknown Test - Sheet1.csv'

def proc_cq_data(times, filename):
    cqs = []
    cqs_res = []

    # extract all cqs
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[1] == 'Closed Quotient':
                continue
            cqs.append(float(row[1]))

    # map cqs to pitch based on time
    for time in times:
        time_cq = round(time * 4) / 4
        i = int(time_cq / 0.05)

        # TODO: Change warning into a fatal error
        try:
            cqs_res.append(cqs[i])
        except:
            print("Warning: Mismatch of pitch and cq data times")

    return cqs_res

cqs_res = proc_cq_data(times, filename)

pprint.pp(cqs_res)
