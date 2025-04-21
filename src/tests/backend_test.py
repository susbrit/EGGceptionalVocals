import os
import pprint

#from src.proc_data import TIME_STEP
#from .context import proc_data
#from .context import utils
from .context import *
def test_proc_pitch():
    total_count = 0
    pfs = []
    pfs.append('src/tests/data/pitch_data/Izzy C Major Scale Mic Only.xlsx')
    pfs.append('src/tests/data/pitch_data/Amit C Major.xlsx')
    pfs.append('src/tests/data/pitch_data/Teresa G Major Scale.xlsx')
    pfs.append('src/tests/data/pitch_data/Shawn A Major Scale.xlsx')

    for pf in pfs:
        print(pf)
        wb = openpyxl.load_workbook(pf)
        times, pitches = utils.pitch.proc_freq_data(wb, TIME_STEP)
        total = len(pitches)
        total_count += total
        pprint.pp(pitches)
        print('total: ', total)
        print('total count: ', total_count)

def test_proc_data(): 
    pf = 'src/tests/data/pitch_data/Izzy C Major Scale Mic Only.xlsx'
    cf = 'src/tests/data/cq_data/dummy_cq_1.csv'
    p_ticks, times, pitches, cqs = proc_data.proc_data(pf, cf)

    print('p-axis ticks:')
    print(p_ticks)
    print('\ntimes:')
    pprint.pp(times)
    print('\npitches:')
    pprint.pp(pitches)
    print('\nCQs')
    pprint.pp(cqs)

def test_proc_data_sets():
    pf = 'src/tests/data/pitch_data/Izzy C Major Scale Mic Only.xlsx'
    cf1 = 'src/tests/data/cq_data/dummy_cq_1.csv'
    cf2 = 'src/tests/data/cq_data/dummy_cq_2.csv'

    # for sake of simplicity, reuse pf for all data sets
    data_sets = [(pf, cf1), (pf, cf2)]

    p_ticks, data_sets_proc = proc_data.proc_data_sets(data_sets)
    print('p-axis ticks:')
    print(p_ticks)
    for keys,values in data_sets_proc.items():
        print('\ndata set:')
        pprint.pp(keys)
        print('\npitch to CQ average:')
        pprint.pp(values)


def test_backend():
    pitch_data = 'src/tests/data/pitch_data/'
    cf = 'src/tests/data/cq_data/dummy_cq_1.csv'

    for pitch_file_name in os.listdir(pitch_data):
        pf = os.path.join(pitch_data, pitch_file_name)
        print(pf)
        
        p_ticks, times, pitches, cqs = proc_data.proc_data(pf, cf)
        
        #test_map_data(pitches, cqs)

# Run tests
#test_proc_pitch()
#test_proc_data()
test_proc_data_sets()
#test_backend()
