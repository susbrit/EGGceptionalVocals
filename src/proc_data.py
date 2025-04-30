import utils.pitch
import utils.cq as cq
import openpyxl
import numpy as np

###############################################################################
# CONSTANTS
###############################################################################

TIME_STEP = 40

'''
Ideal CQ Range for Female
______________
Expected to increase with pitch.
Includes three lists to represent frequencies, LO CQ values, and HI CQ values.
'''
idealCQfemalefreqs = [
         'G3',   'B3',   'D#4',    'G4',    'B4',  'D#5'
        ]

idealCQfemaleLO = [
        24.0, 27.0, 30.0, 33.0, 37.0, 38.0
        ]

idealCQfemaleHI = [
        26.0, 28.0, 31.0, 35.0, 38.0, 41.0
        ]

'''
Ideal CQ Range for Male
_______________________
Expected to be relatively constant regardless of pitch.
(CQ LO, CQ HI)
'''
idealCQmale = (34, 54)

###############################################################################
# HELPER FUNCTIONS
###############################################################################

def trim_data(times, pitches, cqs):
    lens = [len(times), len(pitches), len(cqs)]
    shortlen = min(lens)
    times_res = times[:shortlen]
    pitches_res = pitches[:shortlen]
    cqs_res = cqs[:shortlen]
    return times_res, pitches_res, cqs_res

def find_pitch_bounds(pitches):
    freqs = []
    for p in pitches:
        freqs.append(utils.pitch.get_freq(p))
    
    freq_lo = min(freqs)
    freq_mid = np.median(freqs)
    freq_hi = max(freqs)
    pitch_lo = utils.pitch.get_pitch(freq_lo)
    pitch_mid =utils.pitch.get_pitch(freq_mid)
    pitch_hi = utils.pitch.get_pitch(freq_hi)

    return ((pitch_lo,freq_lo), (pitch_mid,freq_mid), (pitch_hi,freq_hi))

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
        # represent the pitch as frequency for the data point
        freq = utils.pitch.get_freq(pitch)
        pitch2cq_map.append( (freq, cq) )

    return pitch2cq_map

###############################################################################
# FUNCTIONS
###############################################################################

def get_pitch_label(freq):
    '''
    Parameters
    __________
    freq: Mouse cursor position representing a frequency value

    Returns
    _______
    pitch: String representing the pitch note

    Description
    ___________
    Get the pitch note label corresponding to the mouse cursor position. 
    '''
    return utils.pitch.get_pitch(freq)

def proc_data(pitch_file_path, cq_file_path):
    '''
    Parameters
    __________
    pitch_file_path: String path to a .xlsx file of pitch data
    cq_file_path: String path to a .csv file of CQ data

    Returns
    _______
    p_ticks: Tuple of pitch bounds (lo, mid, hi)
    times: Array of timestamps
    pitches: Array of pitch note values
    cqs: Array of CQ weighted average values

    Description
    ___________
    Process a data set of frequency and CQ measurements.

    A processed data set results in four outputs.
    1)  A nested tuple of p-axis graph ticks formatted as 
        ( (pitch_lo,freq_lo),  (pitch_mid, freq_mid), (pitch_hi, freq_hi) )
    2) An array of floats representing timestamps to base ptich and CQ values on.
    3) An array of floats representing CQ values.
    4) An array of strings representing pitch notes.
    5) An array of floats representing frequency values.
    '''
    freq_data = openpyxl.load_workbook(pitch_file_path)

    times, pitches = utils.pitch.proc_freq_data(freq_data, TIME_STEP)
    cqs = cq.proc_cq_data(times, cq_file_path)
    
    if (len(times) != len(pitches)) | (len(times) != len(cqs)):
        print('Warning: Mismatch of shapes for times and CQs')
        times, pitches, cqs = trim_data(times, pitches, cqs)

    # convert pitches to frequencies
    freqs = []
    for pitch in pitches:
        freqs.append(utils.pitch.get_freq(pitch))


    # process pitches into p-axis graph ticks
    p_ticks = find_pitch_bounds(pitches)
    
    return p_ticks, times, cqs, pitches, freqs

def proc_data_sets(data_sets):
    '''
    Parameters
    __________
    data_sets: List of data sets.

    Returns
    _______
    p_ticks: Tuple of pitch bounds (lo, mid, hi)
    data_sets_proc: Dictionary mapping data sets to data points

    Description
    ___________
    Process a list of one or more sets of data. 

    Each data set in the list should be a tuple formatted as (pf, cf) where
    'pf' is a path to a .xlsx file of pitch data and 'cf' is a path to a
    .csv file of CQ data. Each data set should represent a distinct recording
    of the same repertoire or warmup. 

    A processed list of data sets results in two outputs. 
    1)  A nested tuple of p-axis graph ticks formatted as 
        ( (pitch_lo,freq_lo),  (pitch_mid, freq_mid), (pitch_hi, freq_hi) )
    2)  A dictionary mapping data sets, as keys, to a list of 2-D data points.
       Each data point is a tuple formatted as (f, c) where
       'f' is a frequency value and 'c' is a CQ value.
    '''
    data_sets_proc = dict()
    pitches_all = []
    # process each data set into a list of data points
    for set in data_sets:
        # process data set into a map
        p_ticks, times, cqs, pitches, freqs = proc_data(set[0], set[1])
        pitch2cq_map = map_data(pitches, cqs)

        # add map to dictionary
        data_sets_proc[set] = pitch2cq_map

        # collect all pitches from the data sets
        pitches_all += pitches

    # process unioned pitches into p-axis graph ticks
    p_ticks = find_pitch_bounds(pitches_all)
    return p_ticks, data_sets_proc
