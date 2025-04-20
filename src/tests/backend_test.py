import os
import pprint
from .context import proc_data

def test_proc_data(): 
    pf = 'src/tests/data/pitch_data/Izzy C Major Scale Mic Only.xlsx'
    cf = 'src/tests/data/cq_data/dummy_cq_1.csv'
    p_ticks, times, pitches, cqs = proc_data.proc_data(pf, cf)
    print(p_ticks)
    pprint.pp(times)
    pprint.pp(pitches)
    pprint.pp(cqs)

def test_proc_data_sets():
    pf = 'src/tests/data/pitch_data/Izzy C Major Scale Mic Only.xlsx'
    cf1 = 'src/tests/data/cq_data/dummy_cq_1.csv'
    cf2 = 'src/tests/data/cq_data/dummy_cq_2.csv'

    # for sake of simplicity, reuse pf for all data sets
    data_sets = [(pf, cf1), (pf, cf2)]

    p_ticks, data_sets_proc = proc_data.proc_data_sets(data_sets)
    print(p_ticks)
    print(data_sets_proc)

def test_backend():
    pitch_data = 'src/tests/data/pitch_data/'
    cf = 'src/tests/data/cq_data/dummy_cq_1.csv'

    for pitch_file_name in os.listdir(pitch_data):
        pf = os.path.join(pitch_data, pitch_file_name)
        print(pf)
        
        p_ticks, times, pitches, cqs = proc_data.proc_data(pf, cf)
        
        #test_map_data(pitches, cqs)

# Run tests
#test_backend()
test_proc_data()
test_proc_data_sets()
