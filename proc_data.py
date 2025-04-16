import pitch
import cq
import openpyxl
import pprint
import csv
import os

user = "Izzy"
rep_name = "Izzy C Major Scale Mic Only"
freq_data = "data/Izzy C Major Scale Mic Only.xlsx"
cq_data = "data/CQ Unknown Test - Sheet1.csv"
date = '04-10-2025'

def get_path(user, rep, rep_name=None):
    if rep:
        path = 'db/' + user + '/' + 'library/' + rep_name + '/'
    else:
        path = 'db/' + user + '/' + 'warmup/'
    return path

def trim_data(times, pitches, cqs):
    lens = [len(times), len(pitches), len(cqs)]
    shortlen = min(lens)
    times_res = times[:shortlen]
    pitches_res = pitches[:shortlen]
    cqs_res = cqs[:shortlen]
    return times_res, pitches_res, cqs_res

# Output processed time, pitch, and cq data into a file
def proc_new_data(user, rep, freq_data_wb, cq_data, rep_name=None):
    freq_step = 40
    freq_data = openpyxl.load_workbook(freq_data_wb)

    times, pitches = pitch.proc_freq_data(freq_data, freq_step)
    cqs = cq.proc_cq_data(times, cq_data)
    # TODO: DELETE!
    #cqs.append(0.0)
    #cqs.append(0.0)

    # Write processed data into new csv file
    if rep:
        path = get_path(user, 1, rep_name)
        if not os.path.exists(path):
            os.mkdir(path)
    else:
        path = get_path(user, 0)

    filepath = path + date + '.csv'
    header = ['Time', 'Pitch', 'CQ']
    with open(filepath, 'w') as new_data:
        writer = csv.writer(new_data, delimiter=',')
        header = ["Time", "Pitch", "CQ"]
        writer = csv.DictWriter(new_data, fieldnames=header)
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

                times, pitches, cqs = trim_data(times, pitches, cqs)
                n = len(times)
                for i in range(0, n):
                    writer.writerow({'Time': times[i], 'Pitch': pitches[i], 'CQ': cqs[i]})

    return

def retrieve_data(user, rep, date, rep_name=None):
    times = []
    pitches = []
    cqs = []
    
    if rep:
        path = get_path(user, 1, rep_name)
    else:
        path = get_path(user, 0)
        
    filepath = path + date + '.csv'
    try:
        with open(filepath, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader) 

    except:
        if not os.path.exists(filepath):
            print('Error: File', filepath, 'does not exist')
        else:
            print('Error: Unknown')

    n = len(rows)
    for i in range(1, n):
        row = rows[i]
        times.append(row[0])
        pitches.append(row[1])
        cqs.append(row[2])

    return times, pitches, cqs

# Quick run

proc_new_data(user, 0, freq_data, cq_data, rep_name=None)

times, pitches, cqs = retrieve_data(user, 0, date, rep_name=None)

print("\n\nTimes:\n")
pprint.pp(times)
print("\n\nPitches:\n")
pprint.pp(pitches)
print("\n\nCQs:\n")
pprint.pp(cqs)
