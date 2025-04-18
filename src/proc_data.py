import utils.pitch as pitch
import utils.cq as cq
import openpyxl
import numpy as np
import pprint

# CONSTANTS
TIME_STEP = 40

'''
pitch_file_path =  "data/Izzy C Major Scale Mic Only.xlsx"
cq_file_path = "data/CQ Unknown Test - Sheet1.csv"
'''

def find_pitch_bounds(pitches):
    freqs = []
    for p in pitches:
        freqs.append(pitch.get_freq(p))
    
    freq_lo = min(freqs)
    freq_mid = np.median(freqs)
    freq_hi = max(freqs)
    pitch_lo = pitch.get_pitch(freq_lo)
    pitch_mid = pitch.get_pitch(freq_mid)
    pitch_hi = pitch.get_pitch(freq_hi)

    return pitch_lo, pitch_mid, pitch_hi

def trim_data(times, pitches, cqs):
    lens = [len(times), len(pitches), len(cqs)]
    shortlen = min(lens)
    times_res = times[:shortlen]
    pitches_res = pitches[:shortlen]
    cqs_res = cqs[:shortlen]
    return times_res, pitches_res, cqs_res

def map_data(pitches, cqs):
    pitch2i_dict = dict()
    n = len(pitches)

    # map pitches to indices
    for i in range(0, n):
        pitch = pitches[i]
        if pitch not in pitch2i_dict:
            pitch2i_dict[pitch] = [i]
        else:
            pitch2i_dict[pitch].append(i)
    
    # map cqs to pitch
    pitch2cq_dict = dict()
    for pitch in pitch2i_dict:
        cq_vals = []
        pitch_indices = pitch2i_dict[pitch]
        for i in pitch_indices:
            cq_vals.append(cqs[i])
        pitch2cq_dict[pitch] = np.round( np.mean(cq_vals), 2 )
    
    # format mapping into tuples
    pitch2cq_map = []
    for pitch in pitch2cq_dict:
        cq = pitch2cq_dict[pitch]
        pitch2cq_map.append( (pitch, cq) )

    pprint.pp(pitch2cq_map)
    return pitch2cq_map

# Output processed time, pitch, and cq data
def proc_data(pitch_file_path, cq_file_path):
    freq_data = openpyxl.load_workbook(pitch_file_path)

    times, pitches = pitch.proc_freq_data(freq_data, TIME_STEP)
    cqs = cq.proc_cq_data(times, cq_file_path)
    
    if (len(times) != len(pitches)) | (len(times) != len(cqs)):
        print('Warning: Mismatch of shapes for times and CQs')
        times, pitches, cqs = trim_data(times, pitches, cqs)
    
    return times, pitches, cqs

'''
# Quick run
times, pitches, cqs = proc_data(pitch_file_path, cq_file_path)
map_data(pitches, cqs)
print(find_pitch_bounds(pitches))
'''
