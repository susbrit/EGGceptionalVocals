import pitch
import cq
import openpyxl
import pprint
import csv
import os

user = "Izzy"
rep_name = "Izzy C Major Scale Mic Only"
rep_freq_data = "data/Izzy C Major Scale Mic Only.xlsx"
rep_cq_data = "data/CQ Unknown Test - Sheet1.csv"
date = '04-10-2025'

def get_path(user, rep, rep_name=None):
    if rep:
        path = 'db/' + user + '/' + 'library/' + rep_name + '/'
    else:
        path = 'db/' + user + '/' + 'warmup/'
    return path

# Output processed time, pitch, and cq data into a file
def new_repertoire(user, rep_name, rep_freq_data, rep_cq_data):
    freq_step = 40
    freq_data = openpyxl.load_workbook(rep_freq_data)

    times, pitches = pitch.proc_freq_data(freq_data, freq_step)
    cqs = cq.proc_cq_data(times, rep_cq_data)
    # TODO: DELETE!
    cqs.append(0.0)
    cqs.append(0.0)

    # Write processed data into new csv file
    path = get_path(user, 1, rep_name)
    if not os.path.exists(path):
        os.mkdir(path)

    filepath = path + date + '.csv'

    header = ['Time', 'Pitch', 'CQ']
    with open(filepath, 'w') as new_rep:
        writer = csv.writer(new_rep, delimiter=',')
        header = ["Time", "Pitch", "CQ"]
        writer = csv.DictWriter(new_rep, fieldnames=header)
        writer.writeheader()

        n = len(times)
        try:
            for i in range(0, n):
                writer.writerow({'Time': times[i], 'Pitch': pitches[i], 'CQ': cqs[i]})

        except:
            if n != len(pitches):
                print('Warning: Mismatch of shapes for times and pitches')
            if n != len(cqs):
                print('Warning: Mismatch of shapes for times and CQs')
                print(len(times))
                print(len(cqs))

    return

# Quick run

new_repertoire(user, rep_name, rep_freq_data, rep_cq_data)
