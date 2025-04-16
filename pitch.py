import numpy as np
import sys
from intervaltree import IntervalTree

np.set_printoptions(threshold=sys.maxsize)

# Interval tree of frequencies mapping to pitch
def create_tree():
    # Frequency intervals and map of corresponding pitches
    ivs = [
        #Octave 2                     3                    4                    5                    6
        (63.6,67.4,"C2"),     (127.1,134.7,"C3"),  (255.0,273.0,"C4"),  (509.0,538.8,"C5"),  (1017.1,1077.6,"C6"), 
        (67.4,71.4,"C#2"),    (134.7,142.7,"C#3"), (273.0,284.0,"C#4"), (538.8,570.9,"C#5"), (1077.6,1141.7,"C#6"),
        (71.4,75.6,"D2"),     (142.7,151.2,"D3"),  (284.0,304.0,"D4"),  (570.9,604.8,"D5"),  (1141.7,1209.6,"D6"),
        (75.6,80.1,"D#2"),    (151.2,160.2,"D#3"), (304.0,313.0,"D#4"), (604.8,640.8,"D#5"), (1209.6,1281.5,"D#6"),
        (80.1,84.9,"E2"),     (160.2,169.7,"E3"),  (313.0,340.0,"E4"),  (640.8,678.9,"E5"),  (1281.5,1357.7,"E6"),
        (84.9,89.9,"F2"),     (169.7,179.8,"F3"),  (340.0,363.0,"F4"),  (678.9,719.2,"F5"),  (1357.7,1438.4,"F6"),
        (89.9,95.3,"F#2"),    (179.8,190.5,"F#3"), (363.0,381.0,"F#4"), (719.2,762.0,"F#5"), (1438.4,1524.0,"F#6"),
        (95.3,100.9,"G2"),    (190.5,201.8,"G3"),  (381.0,404.0,"G4"),  (762.0,807.3,"G5"),  (1524.0,1614.6,"G6"),
        (100.9,106.9,"G#2"),  (201.8,213.8,"G#3"), (404.0,428.0,"G#4"), (807.3,855.3,"G#5"), (1614.6,1710.6,"G#6"),
        (106.9,113.27,"A2"),  (213.8,226.5,"A3"),  (428.0,456.0,"A4"),  (855.3,906.2,"A5"),  (1710.6,1812.3,"A6"),
        (113.27,120.0,"A#2"), (226.5,240.0,"A#3"), (456.0,480.0,"A#4"), (906.2,960.1,"A#5"), (1812.3,1920.1,"A#6"),
        (120.0,127.1,"B2"),   (240.0,255.0,"B3"),  (480.0,509.0,"B4"),  (960.1,1017.1,"B5"), (1920.1,2034.3,"B6"),
        
        # Undefined
        (0.0, 63.6, "Undefined"), (2034.3, np.inf, "Undefined")
    ]
    
    tree = IntervalTree.from_tuples(ivs)
    return tree

pitch_tree = create_tree()

def get_pitch(freq):
        res = pitch_tree[freq]
        pitch = list(res).pop()[2]
        return pitch


def proc_freq_data(wb, step):
    # call the first sheet in the workbook
    ws = wb.active
    rows = ws.max_row 
    # extract times and pitch frequencies
    ds = 6 # data starts on row 6
    times = []
    freqs = []
    for i in range(ds, rows):
        # zero out any entries with empty frequency values
        time = ws.cell(row=i,column=1).value
        freq = ws.cell(row=i,column=2).value
        
        times.append(time)
        if freq is not None:
            freqs.append(freq)
        else:
            freqs.append(0)

    # get 0.5 sec averages
    times1 = []
    times2 = []
    freqs_med1 = []
    freqs_med2 = []
    for i in range (0, rows-ds, step):
        step_med = i + (step // 2)
        
        if (step_med) < rows-ds:
            times1.append(times[i])
            freqs_med1.append(np.median(freqs[i:i+step]))

        if (step_med + step) < rows-ds:
            times2.append(times[i+step])
            freqs_med2.append(np.median(freqs[step_med:step_med+step]))
        elif step_med < rows-ds:
            times2.append(times[step_med])
            freqs_med2.append(np.median(freqs[i:i+step]))

    # evaluate pitches
    pitches1 = []
    for freq in freqs_med1:
        pitches1.append(get_pitch(freq))

    pitches2 = [] 
    for freq in freqs_med2:
        pitches2.append(get_pitch(freq))

    times_res = []
    times_res.append(times1[0])
    pitches_res = []
    pitches_res.append(pitches1[0])
    for i in range(1, len(pitches1)):
        if ( (pitches1[i] != pitches2[i]) & (pitches1[i] != pitches2[i-1]) ):
            times_res.append(times2[i])
            pitches_res.append(pitches2[i])
        else:
            times_res.append(times1[i])
            pitches_res.append(pitches1[i])

        # Remove repeated data entries
        if times_res[-1] == times_res[-2]:
            times_res.pop()
            pitches_res.pop()
    
    return times_res, pitches_res
