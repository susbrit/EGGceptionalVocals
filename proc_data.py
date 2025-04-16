import pitch
import cq
import openpyxl
import pprint

# CONSTANTS
TIME_STEP = 40

pitch_file_path =  "data/Izzy C Major Scale Mic Only.xlsx"
cq_file_path = "data/CQ Unknown Test - Sheet1.csv"

'''
def get_path(user, rep, rep_name=None):
    if rep:
        path = 'db/' + user + '/' + 'library/' + rep_name + '/'
    else:
        path = 'db/' + user + '/' + 'warmup/'
    return path
'''

def trim_data(times, pitches, cqs):
    lens = [len(times), len(pitches), len(cqs)]
    shortlen = min(lens)
    times_res = times[:shortlen]
    pitches_res = pitches[:shortlen]
    cqs_res = cqs[:shortlen]
    return times_res, pitches_res, cqs_res

# Output processed time, pitch, and cq data
def proc_data(pitch_file_path, cq_file_path):
    freq_data = openpyxl.load_workbook(pitch_file_path)

    times, pitches = pitch.proc_freq_data(freq_data, TIME_STEP)
    cqs = cq.proc_cq_data(times, cq_file_path)
    
    if (len(times) != len(pitches)) | (len(times) != len(cqs)):
        print('Warning: Mismatch of shapes for times and CQs')
        times, pitches, cqs = trim_data(times, pitches, cqs)
    
    return times, pitches, cqs
