import csv
import openpyxl
import pprint
import numpy as np
from pitch import proc_freq_data

# hardcoded wb file
wb = openpyxl.load_workbook('data/Izzy C Major Scale Mic Only.xlsx')
times, pitches = proc_freq_data(wb, 40)

filename = 'data/CQ Unknown Test - Sheet1.csv'

def get_cq_avg(cq_times, cqs):
    cqs_res = []

    for i in range(0, len(cq_times)-1):
        j = int(cq_times[i] / 0.05)
        k = int(cq_times[i+1] / 0.05)
        step = k - j

        try:
            weights = []
            for n in range(0, step):
                w = 1 / (n+1)
                weights.append(w)

            cq_avg = np.average(cqs[j:k], axis=None, weights=weights)
            clean_cq_avg = float(np.round(cq_avg, 2))
            cqs_res.append(clean_cq_avg)
        
        except:
            if step == 0:
                print("Warning: Repeated timestamp")
                continue

    return cqs_res

def proc_cq_data(times, filename):
    cqs = []
    cqs_res = []

    # extract all cqs
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        for row in rows:
            if row[1] == 'Closed Quotient':
                continue
            cqs.append(float(row[1]))

    # map cqs to pitch based on time
    cq_times = []
    for time in times:
        time_cq = round(time * 4) / 4
        cq_times.append(time_cq)
    
    cqs_res = get_cq_avg(cq_times, cqs)
    return cqs_res

cqs_res = proc_cq_data(times, filename)

pprint.pp(cqs_res)
