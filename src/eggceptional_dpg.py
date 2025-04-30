import dearpygui.dearpygui as dpg
import pygame
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
import simpleaudio as sa
import numpy as np
import math
import pandas as pd
import sqlite3
import proc_data

open_window = None
defined_windows = ["PLAYBACK_WINDOW", "WELCOME_WINDOW", "LIBRARY_WINDOW", "ADD_RECORDING_WINDOW", "TUTORIAL_WINDOW", "ANALYSIS_WINDOW"]

#sqlite database
db = None

# id of recording currently loaded
loaded_recording_id = -1

# array of all pitches

# TEMPORARY VALUES: we want to get this data from the sqlite database rather than hard storing
loaded_cq_file = None
loaded_audio_file = None
loaded_pitch_file = None
loaded_file_name = ""

# switch from open_window to window "switching_to"
# where "switching_to" is a string from global array defined_windows
def switch_window(switching_to):
  global open_window
  global defined_windows
  if switching_to not in defined_windows:
    print(f"ERROR: window {switching_to} does not exist!")
    return

  # first, close existing window
  # switching_from may equal None on app initialization
  if open_window != None:
    if switching_to == open_window.get_window_id():
      print(f"Hmm, you tried to open {switching_to} multiple times in a row")
      return
    try:
      # if a window needs any extra cleanup in addition to deletion
      if hasattr(open_window, "hide"):
        open_window.hide()
      # dpg delete all child windows of primary window
      children = dpg.get_item_children("Primary Window", 1)  # slot 1: all regular children
      if children:
          for child in children:
              item_type = dpg.get_item_type(child)
              if item_type == "mvAppItemType::mvChildWindow":
                  dpg.delete_item(child)
    except:
      print("ERROR: could not hide open window?")

  # now open new window
  new_window = None
  if switching_to == "PLAYBACK_WINDOW":
    new_window = AudioPlayer()
  elif switching_to == "WELCOME_WINDOW":
    new_window = WelcomeScreen()
  elif switching_to == "LIBRARY_WINDOW":
    new_window = LibraryWindow()
  elif switching_to == "ADD_RECORDING_WINDOW":
    new_window = AddRecordingWindow()
  elif switching_to == "TUTORIAL_WINDOW":
    new_window = TutorialWindow()
  elif switching_to == "ANALYSIS_WINDOW":
    new_window = AnalysisWindow()
  
  open_window = new_window

# basic sqlite database to keep track of user's repertoire
class RepertoireDatabase:
  def __init__(self, db_name="repertoire.db"):
    self.db_name = db_name
    self.create_tables()

  def create_tables(self):
    with sqlite3.connect(self.db_name) as conn:
      cursor = conn.cursor()
      # songs table: this contains each possible song, of which there can be any number of recordings 
      cursor.execute("""
        CREATE TABLE IF NOT EXISTS Songs (
          song_id INTEGER PRIMARY KEY AUTOINCREMENT,
          song_name TEXT NOT NULL
        )
      """)
      # recordings table: each individual recording corresponds to a different song
      cursor.execute("""
        CREATE TABLE IF NOT EXISTS Recordings (
          recording_id INTEGER PRIMARY KEY AUTOINCREMENT,
          song_id INTEGER NOT NULL,
          recording_name TEXT NOT NULL,
          date TEXT NOT NULL,
          cq_file_path TEXT NOT NULL,
          pitch_file_path TEXT NOT NULL,
          audio_file_path TEXT NOT NULL,
          FOREIGN KEY (song_id) REFERENCES Songs (song_id) ON DELETE CASCADE
        )
      """)
      conn.commit()

  def insert_song(self, song_name):
    with sqlite3.connect(self.db_name) as conn:
      cursor = conn.cursor()
      cursor.execute("INSERT INTO Songs (song_name) VALUES (?)", (song_name,))
      conn.commit()
      return cursor.lastrowid

  def insert_recording(self, song_id, recording_name, date, cq_file_path, pitch_file_path, audio_file_path):
    with sqlite3.connect(self.db_name) as conn:
      cursor = conn.cursor()
      cursor.execute(
        "INSERT INTO Recordings (song_id, recording_name, date, cq_file_path, pitch_file_path, audio_file_path) VALUES (?, ?, ?, ?, ?, ?)",
        (song_id, recording_name, date, cq_file_path, pitch_file_path, audio_file_path)
      )
      conn.commit()
      return cursor.lastrowid

  def get_all_songs(self):
    with sqlite3.connect(self.db_name) as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT song_id, song_name FROM Songs")
      songs = cursor.fetchall()
      return songs
      # result = []
      # for song in songs:
      #   result.append(song_info)
      # return result

  # returns array with details for all recordings corresponding to a given song
  def get_recordings_from_song(self, song_id):
    with sqlite3.connect(self.db_name) as conn:
      cursor = conn.cursor()
      # Get all recordings for this song
      cursor.execute(
        "SELECT recording_id, recording_name, date FROM Recordings WHERE song_id = ?",
        (song_id,)
      )
      recordings = cursor.fetchall()
      return [
          {"recording_id": r[0], "recording_name": r[1], "date": r[2], "file_path": r[3]} for r in recordings
        ]

  def get_all_recordings(self):
    try:
      with sqlite3.connect(self.db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
          SELECT r.recording_id, r.recording_name, r.date, s.song_name
          FROM Recordings r
          JOIN Songs s ON r.song_id = s.song_id
          ORDER BY r.date DESC
        """)
        recordings = cursor.fetchall()
        return [
          {
            "recording_id": r[0],
            "recording_name": r[1],
            "date": r[2],
            "song_name": r[3]
          } for r in recordings
        ]
    except sqlite3.Error as e:
      print(f"Error in get_all_recordings: {e}")
      return []

  # given id of recording, returns all details for that recording
  def get_recording_by_id(self, recording_id):
    try:
      with sqlite3.connect(self.db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
          SELECT r.recording_id, r.recording_name, r.date, r.cq_file_path, r.pitch_file_path, r.audio_file_path, r.song_id, s.song_name
          FROM Recordings r
          JOIN Songs s ON r.song_id = s.song_id
          WHERE r.recording_id = ?
        """, (recording_id,))
        recording = cursor.fetchone()
        if not recording:
          print(f"No recording found for recording_id={recording_id}")
          return None
        return {
          "recording_id": recording[0],
          "recording_name": recording[1],
          "date": recording[2],
          "cq_file_path": recording[3],
          "pitch_file_path": recording[4],
          "audio_file_path": recording[5],
          "song_id": recording[6],
          "song_name": recording[7],
        }
    except sqlite3.Error as e:
      print(f"Database error in get_recording_by_id: {e}")
      return None

class AudioPlayer:
  # CONSTANTS
  SECONDS_PER_ROW = 10
  BOTTOM_PANEL_HEIGHT = 60
  PLAY_BUTTON_RADIUS = 20

  # global value for tracking loaded audio
  loaded_audio = dict()
  """
  loaded_audio = {
      "file_path_name",
      "is_playing",
      "duration",
      "current_time_index",
      "pause_event"
  }
  """
  #number of table rows
  rows_in_table = 0
  #number of plots per table row
  plots_per_row = 0

  #2d array of plots in the table
  #table_plots = []

  #array of ids of plot cursors to update
  plot_cursors = []
  #array of ids of hovering cursors
  hover_cursors = []

  # cursor styling
  cursor_red = None
  cursor_gray = None
  def __init__(self):
    pygame.mixer.init()
    with dpg.child_window(tag="Audio Player Window", parent="Primary Window"):
        dpg.add_text(default_value="name unknown", tag="selected_file_name")
        with dpg.child_window(tag="waveform_plot", width=-1):
            dpg.add_table(header_row=False, tag="plot_display_table", width=-1, borders_innerH=True)

        with dpg.child_window(tag="bottom_bar", width=-1, height=self.BOTTOM_PANEL_HEIGHT):
            dpg.add_button(label="Play", tag="play_button", callback=self.toggle_play_pause)
            dpg.add_text("00:00/00:00", tag="playtime_status_text")
            dpg.add_button(label="Reset", tag="reset_play_button", callback=self.reset_play)

    with dpg.theme() as self.cursor_red:
        with dpg.theme_component():
            dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 0, 0, 255), category=dpg.mvThemeCat_Plots)

    with dpg.theme() as self.cursor_gray:
        with dpg.theme_component():
            dpg.add_theme_color(dpg.mvPlotCol_Line, (100, 100, 100, 255), category=dpg.mvThemeCat_Plots)

    self.on_window_resize()
    # load cq, pitch, and audio files; created corresponding plots
    self.load_selected_files()
    self.create_cursor_set(0)

  def get_window_id(self):
    return "PLAYBACK_WINDOW"

  # TEMP FUNCTION
  def back_to_menu(self):
    switch_window("WELCOME_WINDOW")

  def hide(self):
    pygame.mixer.quit()

  # event-triggered functions, to be called by AppManager
  def on_render_loop(self):
    if self.loaded_audio and "is_playing" in self.loaded_audio and self.loaded_audio["is_playing"]:
      self.update_position_label()
      self.update_cursor_motion()

  def on_window_resize(self):
    new_height = dpg.get_viewport_height() - 2.25*self.BOTTOM_PANEL_HEIGHT
    dpg.set_item_height("waveform_plot", new_height)
    # center play button & playtime text
    screen_center = int(dpg.get_viewport_width() / 2)
    play_button_top = int(self.BOTTOM_PANEL_HEIGHT / 2 - self.PLAY_BUTTON_RADIUS)
    #playtime_text_top = play_button_top + PLAY_BUTTON_RADIUS * 2
    dpg.set_item_pos("play_button", [screen_center - self.PLAY_BUTTON_RADIUS, play_button_top])

  def on_mouse_move(self):
    self.update_hover_cursor()

  def on_mouse_release(self):
    self.jump_to_hover_pos()

  def update_position_label(self):
    if self.loaded_audio == None:
      return

    if not self.loaded_audio["is_playing"]:
      pos = self.loaded_audio["current_time_index"]
    else:
      pos = pygame.mixer.music.get_pos() + self.loaded_audio["current_time_index"]

    # if audio is done playing, stop updating
    if self.loaded_audio["is_playing"] and not pygame.mixer.music.get_busy():
      self.reset_play()
      return
    # ms to s for position
    minutes = self.get_minutes(pos)
    seconds = self.get_seconds_remainder(pos)
    # ms to s for duration
    dur_minutes = self.get_minutes(self.loaded_audio["duration"])
    dur_seconds = self.get_seconds_remainder(self.loaded_audio["duration"])
    dpg.set_value("playtime_status_text", f"{minutes:02d}:{seconds:02d}/{dur_minutes:02d}:{dur_seconds:02d}")

  def update_cursor_motion(self):
    if self.loaded_audio == None:
      return

    if self.loaded_audio:
      if not self.loaded_audio["is_playing"]:
        pos = self.loaded_audio["current_time_index"] / 1000
      else:
        pos = (pygame.mixer.music.get_pos() + self.loaded_audio["current_time_index"]) / 1000
    else:
      return
    if pos > 0 and pos <= self.loaded_audio["duration"]:
      row_number = int(pos // self.SECONDS_PER_ROW)
      # given row number, check if the first cursor in the area is in correct row
      correct_cursor_parent = f"y_axis_{row_number}_0"
      # if not, delete all cursors and create new ones in the next row
      if dpg.get_item_parent(self.plot_cursors[0]) != dpg.get_alias_id(correct_cursor_parent):
        self.create_cursor_set(row_number)
        dpg.set_y_scroll("waveform_plot", dpg.get_y_scroll("waveform_plot")+950) #TEMP hardcoded for demo
      # update position of all cursors
      for cursor_id in self.plot_cursors:
        dpg.set_value(cursor_id, [[pos]])

  # on mousemove, if hovering over a plot, create a new cursor at position
  def update_hover_cursor(self):
    # only can hover/scroll if there's audio to play
    if self.loaded_audio == None:
      return

    # empty table check (probably superfluous)
    if (self.rows_in_table == 0 or self.plots_per_row == 0):
      return

    # delete any previous hover cursors
    for cursor_id in self.hover_cursors:
      dpg.delete_item(cursor_id)
    self.hover_cursors.clear()
    # loop over plots, determine if any of them have mouse hovering
    for i in range(self.rows_in_table):
      for j in range(self.plots_per_row):
        plot_id = f"waveform_{i}_{j}"
        if not dpg.does_item_exist(plot_id):
          print(f"Error: {plot_id} is not a valid id for a plot right now. We have {self.rows_in_table} rows and {self.plots_per_row} plots per row?")
          return
        # if plot has hover, create a new cursor on all plots in that row using that x coordinate
        if dpg.is_item_hovered(plot_id):
          mouse_pos = dpg.get_plot_mouse_pos()
          for k in range(self.plots_per_row):
            hover_tag = f"hover_cursor_{i}_{k}"
            dpg.add_inf_line_series([mouse_pos[0]], label="vertical line", parent=f"y_axis_{i}_{k}", tag=hover_tag)
            self.hover_cursors.append(hover_tag)
            dpg.bind_item_theme(f"hover_cursor_{i}_{k}", self.cursor_gray)
          return

  # on mouseup, if there's a hover cursor, jump to that position
  def jump_to_hover_pos(self):
    if self.loaded_audio == None:
      return
    # mouse is not on the plot
    if len(self.hover_cursors) == 0:
        return
    x_pos = dpg.get_value(self.hover_cursors[0])[0][0]
    # use the name of the cursor tag to extract the row number to jump to
    row_num = int(self.hover_cursors[0].split('_')[2])
    self.create_cursor_set(row_num, x_pos)
    self.set_is_playing(False)
    self.loaded_audio["current_time_index"] = x_pos * 1000
    self.update_position_label()

  # generates visual of waveform for the selected audio file
  # splits waveform into separate rows if necessary (based on SECONDS_PER_ROW)
  def load_selected_files(self):
    global db
    global loaded_recording_id

    #load recording details given id
    recording_details = db.get_recording_by_id(loaded_recording_id)

    # set label for song
    dpg.set_value("selected_file_name", f"Song Name: {recording_details['song_name']}; Recording Name: {recording_details['recording_name']} on {recording_details['date']}")

    # number of plots per row depends on how many input files are defined, but is hardcoded for now
    # TODO error checking
    self.plots_per_row = 3 

    #TODO duration is set by audio, which assumes proper trimming w other files
    duration = 0

    # set up audio file
    if recording_details['audio_file_path'] != None:
      self.loaded_audio["file_path_name"] = recording_details['audio_file_path']
      self.loaded_audio["is_playing"] = False
      self.loaded_audio["current_time_index"] = 0

      # Load the audio file
      audio = AudioSegment.from_file(self.loaded_audio["file_path_name"])
      samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
      if audio.channels > 1:
        samples = samples.reshape(-1, audio.channels)[:, 0].copy()  

      # Normalize for better visualization (limiting y axis to -1 to 1 range)
      samples /= np.max(np.abs(samples))

      # calculate total duration of audio input & number of lines to display
      duration = len(samples) / audio.frame_rate
      self.loaded_audio["duration"] = duration * 1000
      dur_minutes = self.get_minutes(self.loaded_audio["duration"])
      dur_seconds = self.get_seconds_remainder(self.loaded_audio["duration"])
      dpg.set_value("playtime_status_text", f"00:00/{dur_minutes:02d}:{dur_seconds:02d}")
      num_lines = math.ceil(duration / self.SECONDS_PER_ROW)


      # process input pitch and CQ spreadsheet
      p_ticks, times, pitches, cqs = proc_data.proc_data(
        recording_details['pitch_file_path'],
        recording_details['cq_file_path']
      )

      times_array = np.array(times)
      cqs_array = np.array(cqs)
      pitches_array = np.array(pitches)

      #calculate graph bounds for pitch-- a little outside of lowest/highest values
      min_pitch_bound = .9 * p_ticks[0][1]
      max_pitch_bound = 1.1 * p_ticks[2][1]

      # process input CQ spreadsheet
    else:
      self.loaded_audio = None

    if pygame.mixer.music.get_busy():
      pygame.mixer.music.stop()

    # determine number of rows to be added to the table
    self.rows_in_table = math.ceil(duration / self.SECONDS_PER_ROW)

    # not sure why this line is necessary, but it is
    dpg.add_table_column(parent="plot_display_table")

    # loop over each line and create a plot for each time chunk (based on SECONDS_PER_ROW)
    for i in range(self.rows_in_table):
      # limits of time range per chunk
      min_time = i * self.SECONDS_PER_ROW
      max_time = min(min_time + self.SECONDS_PER_ROW, math.floor(duration))

      # if extra audio is <1 second, cut it off
      if (max_time-min_time == 0):
          self.rows_in_table = self.rows_in_table - 1
          break
      
      # Generate time values for the CQ and pitch values
      time_mask = (times_array >= min_time) & (times_array <= max_time)
      time_chunk = times_array[time_mask]
      cq_value_chunk = cqs_array[time_mask]
      pitch_value_chunk = pitches_array[time_mask]

      # Generate X values for audio data (time axis)
      if recording_details['audio_file_path'] != None:
        audio_time = np.linspace(min_time, max_time, num=(max_time-min_time)*audio.frame_rate)
        chunk_samples_audio = samples[min_time*audio.frame_rate:max_time*audio.frame_rate]

      # container for this line
      if dpg.does_item_exist("plot_display_table"):
        with dpg.table_row(tag=f"display_row_{i}", parent="plot_display_table", height=950):
          with dpg.group(horizontal=False):
            plot_num = 0
            # plot the CQ waveform
            if recording_details['cq_file_path'] != None:
              with dpg.plot(tag=f"waveform_{i}_{str(plot_num)}", height=260, width=-1):
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, tag=f"x_axis_{i}_{str(plot_num)}")
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Closed Quotient", tag=f"y_axis_{i}_{str(plot_num)}")
                dpg.set_axis_ticks(dpg.last_item(), (("0.1", 0.1), ("0.2", 0.2), ("0.3", 0.3), ("0.4", 0.4), ("0.5", 0.5), ("0.6", 0.6), ("0.7", 0.7), ("0.8", 0.8), ("0.9", 0.9), ("1.00", 1)))
                #dpg.add_line_series(time, .5*np.sin(5*time), label="Arbitrary Data", parent=y_axis)
                dpg.add_line_series(time_chunk, cq_value_chunk, label="Closed Quotient", parent=y_axis)
                # fix time and amplitude so that the user can't scroll around
                dpg.set_axis_limits(f"x_axis_{i}_{str(plot_num)}", min_time, max_time)
                dpg.set_axis_limits(f"y_axis_{i}_{str(plot_num)}", 0, 1)
                plot_num = plot_num + 1

            # plot the pitch waveform
            if recording_details['pitch_file_path'] != None:
              with dpg.plot(tag=f"waveform_{i}_{str(plot_num)}", height=260, width=-1):
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, tag=f"x_axis_{i}_{str(plot_num)}")
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Pitch Frequency (Hz)", tag=f"y_axis_{i}_{str(plot_num)}")
                dpg.set_axis_ticks(dpg.last_item(), p_ticks)
                #dpg.add_line_series(time_chunk, pitch_value_chunk, label="Pitch Frequency", parent=y_axis)
                #TODO current backend is sending note names rather than frequencies to graph
                dpg.add_line_series(time_chunk, cq_value_chunk, label="Pitch Frequency", parent=y_axis)
                # fix time and amplitude so that the user can't scroll around
                dpg.set_axis_limits(f"x_axis_{i}_{str(plot_num)}", min_time, max_time)
                # TODO this limit is hard coded right now
                dpg.set_axis_limits(f"y_axis_{i}_{str(plot_num)}", min_pitch_bound, max_pitch_bound)
                plot_num = plot_num + 1

            # plot the audio waveform
            if recording_details['audio_file_path'] != None:
              with dpg.plot(tag=f"waveform_{i}_{str(plot_num)}", height=200, width=-1):
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{i}_{str(plot_num)}")
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Audio Signal", tag=f"y_axis_{i}_{str(plot_num)}")
                dpg.add_line_series(audio_time, chunk_samples_audio, label="Audio Signal", parent=y_axis)
                # fix time and amplitude so that the user can't scroll around
                dpg.set_axis_limits(f"x_axis_{i}_{str(plot_num)}", min_time, max_time)
                dpg.set_axis_limits(f"y_axis_{i}_{str(plot_num)}", -1, 1)
      else:
        print("Error: Table 'plot_display_table' not found")
        return
          
  # Where row_num is the row in table where cursor is initialized to
  def create_cursor_set(self, row_num, x_value=0):
    if self.loaded_audio == None:
      return

    # Initialize cursor
    for cursor_id in self.plot_cursors:
      dpg.delete_item(cursor_id)
    self.plot_cursors.clear()
    for i in range (self.plots_per_row):
      cursor_tag = f"playback_cursor_{i}"
      if not dpg.does_item_exist(f"y_axis_{row_num}_{i}"):
        print(f"Error: cannot create a new cursor, because y_axis_{row_num}_{i} does not exist to be a parent")
      new_line = dpg.add_inf_line_series([0], tag=cursor_tag, label="vertical line", parent=f"y_axis_{row_num}_{i}")
      dpg.bind_item_theme(new_line, self.cursor_red)
      self.plot_cursors.append(cursor_tag)
      dpg.set_value(cursor_tag, [[x_value]])

  # sets loaded_audio["is_playing"] to given value, and updates play button text
  def set_is_playing(self, playing_value):
    if self.loaded_audio == None:
      return

    # ignore duplicate settings
    if "is_playing" in self.loaded_audio and self.loaded_audio["is_playing"] == playing_value:
      return
    self.loaded_audio["is_playing"] = playing_value
    # play music
    if playing_value:
      dpg.set_item_label("play_button", "Pause")
      if self.loaded_audio["current_time_index"] == None:
          self.loaded_audio["current_time_index"] = 0
      pygame.mixer.music.load(self.loaded_audio["file_path_name"])
      pygame.mixer.music.play(start=self.loaded_audio["current_time_index"]/1000)  # Convert ms to seconds
    # pause music
    else:
      dpg.set_item_label("play_button", "Play")
      self.loaded_audio["current_time_index"] = pygame.mixer.music.get_pos() + self.loaded_audio["current_time_index"]
      pygame.mixer.music.pause()

  # Toggle play/pause of loaded audio on button click
  def toggle_play_pause(self):
    if self.loaded_audio == None or self.loaded_audio["is_playing"] == None:
      return

    # going from play state to pause state
    if self.loaded_audio["is_playing"]:
      self.set_is_playing(False)
    # going from pause state to play state
    else:
      self.set_is_playing(True)

  # return to timestamp 0 of given audio file
  def reset_play(self):
    if self.loaded_audio == None:
      return

    self.set_is_playing(False)
    self.loaded_audio["current_time_index"] = 0
    self.update_position_label()
    self.create_cursor_set(0)
    dpg.set_y_scroll("waveform_plot", 0)

  # UTILITIES #
  # given a value in miliseconds, returns the number of minutes
  def get_minutes(self, ms_value):
    return int(ms_value // 60000)

  # given a value in miliseconds, returns the number of seconds in remainder
  # eg: a value that is, in total, 6 minutes 20 seconds will return 20
  def get_seconds_remainder (self, ms_value):
    return int((ms_value % 60000) // 1000)

class AnalysisWindow:
  def __init__(self):
    global db
    global loaded_recording_id

    #load recording details given id
    recording_details = db.get_recording_by_id(loaded_recording_id)

    # load analysis for given song
    # process input pitch and CQ spreadsheet
    p_ticks, data_sets_proc = proc_data.proc_data_sets([(
      recording_details['pitch_file_path'],
      recording_details['cq_file_path']
    )])

    print(p_ticks)
    print(data_sets_proc)
    print(data_sets_proc[(
      recording_details['pitch_file_path'],
      recording_details['cq_file_path']
    )])

    with dpg.child_window(tag="Analysis Window", parent="Primary Window"):
      dpg.add_text("View CQ data corresponding to sung pitches.")
      dpg.add_text(f"Song Name: {recording_details['song_name']}; Recording Name: {recording_details['recording_name']} on {recording_details['date']}")

  def get_window_id(self):
    return "ANALYSIS_WINDOW"

# window where user can add a new recording (CQ, audio, or both)
# TODO: expand to allow editing details of a preexisting recording
class AddRecordingWindow:
  selected_cq_file = None
  selected_audio_file = None
  selected_pitch_file = None
  selected_song = None
  def __init__(self):
    global db
    with dpg.child_window(tag="Add Recording Window", parent="Primary Window"):
      dpg.add_text("Add a new recorded piece to your repertoire library:")

      dpg.add_text("\n\nWhat song is this a recording of?")
      dpg.add_listbox(callback=self.select_song, tag="song_listbox")
      dpg.add_input_text(hint="Create New Song", tag="new_song_input")
      dpg.add_button(label="Add Song", callback=self.create_song)

      dpg.add_text("\n\nNo CQ file selected.", tag="cq_file_name")
      dpg.add_button(label="Select CQ data file", callback=lambda: dpg.show_item("cq_file_dialog"))

      dpg.add_text("\n\nNo pitch data file selected.", tag="pitch_file_name")
      dpg.add_button(label="Select pitch data file", callback=lambda: dpg.show_item("pitch_file_dialog"))

      dpg.add_text("\n\nNo audio file selected.", tag="audio_file_name")
      dpg.add_button(label="Select audio data file", callback=lambda: dpg.show_item("audio_file_dialog"))

      dpg.add_text("\n\nGive your recording a name:")
      dpg.add_input_text(hint="Untitled Recording", tag="title_input")

      dpg.add_text("\n\n")
      dpg.add_button(label="Submit", callback=self.submit_data)

      with dpg.file_dialog(directory_selector=False, show=False, callback=self.select_audio, id="audio_file_dialog", width=700 ,height=400):
            dpg.add_file_extension("Source files (*.mp3 *.wav){.mp3,.wav}", color=(0, 255, 255, 255))
      # CQ must be a .csv file
      with dpg.file_dialog(directory_selector=False, show=False, callback=self.select_cq, id="cq_file_dialog", width=700 ,height=400):
            dpg.add_file_extension("Source files (*.csv){.csv}", color=(0, 255, 255, 255))
      # pitch must be a .xlsx file
      with dpg.file_dialog(directory_selector=False, show=False, callback=self.select_pitch, id="pitch_file_dialog", width=700 ,height=400):
            dpg.add_file_extension("Source files (*.xlsx){.xlsx}", color=(0, 255, 255, 255))

    self.set_song_list_values()

  def get_window_id(self):
    return "ADD_RECORDING_WINDOW"

  # dpg handles file dialogs differently than other components,
  # so it's necessary to explicitly delete them to prevent errors
  def hide(self):
    dpg.delete_item("audio_file_dialog")
    dpg.delete_item("cq_file_dialog")
    dpg.delete_item("pitch_file_dialog")

  def set_song_list_values(self):
    # define values for song listbox 
    dpg.configure_item("song_listbox", items=[song[1] for song in db.get_all_songs()])

  def create_song(self, sender, app_data):
    global db
    db.insert_song(dpg.get_value("new_song_input"))
    dpg.set_value("new_song_input", "")
    self.set_song_list_values()

  def select_song(self, sender, app_data):
    self.selected_song = app_data

  def select_cq(self, sender, app_data):
    if not app_data["file_path_name"]:
      return
    file_path_name = app_data["file_path_name"]
    file_name = app_data["file_name"]
    self.selected_cq_file = file_path_name
    dpg.set_value("cq_file_name", f"\n\n{file_name}")

  def select_pitch(self, sender, app_data):
    if not app_data["file_path_name"]:
      return
    file_path_name = app_data["file_path_name"]
    file_name = app_data["file_name"]
    self.selected_pitch_file = file_path_name
    dpg.set_value("pitch_file_name", f"\n\n{file_name}")

  def select_audio(self, sender, app_data):
    if not app_data["file_path_name"]:
      return
    file_path_name = app_data["file_path_name"]
    file_name = app_data["file_name"]
    self.selected_audio_file = file_path_name
    dpg.set_value("audio_file_name", f"\n\n{file_name}")

  def submit_data(self):
    # global loaded_cq_file
    # global loaded_pitch_file
    # global loaded_audio_file
    # global loaded_file_name
    global loaded_recording_id
    global db

    # must select at least one file to display, and must select a corresponding song
    # if (self.selected_audio_file == None and self.selected_cq_file == None and self.selected_pitch_file == None) or self.selected_song == None:
    if (self.selected_audio_file == None and self.selected_cq_file == None and self.selected_pitch_file == None):
      print(f"Couldn't open playback page without file input (received: {self.selected_audio_file} {self.selected_cq_file} {self.selected_pitch_file} {self.selected_song}")
      return
    
    # loaded_cq_file = self.selected_cq_file
    # loaded_pitch_file = self.selected_pitch_file
    # loaded_audio_file = self.selected_audio_file
    # loaded_file_name = dpg.get_value("title_input")

    #TODO make this more smooth if possible - currently, use sequencing of song name list to determine song_id
    song_id = -1
    list_config = dpg.get_item_configuration("song_listbox")    
    for i, item in enumerate(list_config['items']):        
      if item == self.selected_song:
        song_id = i+1

    # error finding matching id
    if song_id == -1:
      print("ERROR: could not determine song_id for selection, picking default")
      song_id = 0
    
    recording_title = dpg.get_value("title_input")
    if recording_title == None:
      recording_title = "Untitled Recording"
    #TODO date generation/setting
    loaded_recording_id = db.insert_recording(song_id, recording_title, "2025-04-16", self.selected_cq_file, self.selected_pitch_file, self.selected_audio_file)
    switch_window("PLAYBACK_WINDOW")

class LibraryWindow:
  def __init__(self):
    with dpg.child_window(tag="Library Window", parent="Primary Window"):
      dpg.add_text("All Your Recordings")
      with dpg.table(
        tag="recordings_table",
        header_row=True,
        borders_innerH=True,
        borders_innerV=True,
        borders_outerH=True,
        borders_outerV=True,
        resizable=True
      ):
        # Define columns
        dpg.add_table_column(label="Song Name")
        dpg.add_table_column(label="Recording Name")
        dpg.add_table_column(label="Date")
        dpg.add_table_column(label="Open Recording")
        dpg.add_table_column(label="Analyze Recording")
      self.populate_table()

  def select_recording(self, sender, app_data, user_data):
    global loaded_recording_id
    loaded_recording_id = user_data
    switch_window("PLAYBACK_WINDOW")

  def select_analysis(self, sender, app_data, user_data):
    global loaded_recording_id
    loaded_recording_id = user_data
    switch_window("ANALYSIS_WINDOW")

  def populate_table(self):
    global db
    # Fetch recordings
    recordings = db.get_all_recordings()
    for rec in recordings:
      with dpg.table_row(parent="recordings_table"):
        dpg.add_text(rec["song_name"])
        dpg.add_text(rec["recording_name"])
        dpg.add_text(rec["date"])
        dpg.add_button(
          label="Open",
          callback=self.select_recording,
          user_data=rec["recording_id"]
        )
        dpg.add_button(
          label="Analyze",
          callback=self.select_analysis,
          user_data=rec["recording_id"]
        )

  def get_window_id(self):
    return "LIBRARY_WINDOW"

class WelcomeScreen:
  def __init__(self):
    with dpg.child_window(label="Welcome", tag="Welcome Window", parent="Primary Window"):
      dpg.add_text("Welcome to EGGceptional Vocals!")
      dpg.add_button(label="Add a new recording", callback=self.create_add_recording_window)
      dpg.add_button(label="View your repertoire", callback=self.create_library_window)

  def get_window_id(self):
    return "WELCOME_WINDOW"

  def create_add_recording_window(self):
    switch_window("ADD_RECORDING_WINDOW")

  def create_library_window(self):
    switch_window("LIBRARY_WINDOW")

class TutorialWindow:
  def __init__(self):
    with dpg.child_window(tag="Tutorial Window", parent="Primary Window"):
      dpg.add_text("Insert your tutorial here")

  def get_window_id(self):
    return "TUTORIAL_WINDOW"

class AppManager:
  def __init__(self):
    dpg.create_context()
    dpg.create_viewport(title='Test App', width=600, height=400)
    with dpg.window(tag="Primary Window"):
        with dpg.menu_bar():
          dpg.add_menu_item(label="Home", callback=self.switch_to_welcome)
          dpg.add_menu_item(label="Tutorial", callback=self.switch_to_tutorial)
          dpg.add_menu_item(label="Add Recording", callback=self.switch_to_add_recording)
          dpg.add_menu_item(label="Library", callback=self.switch_to_library)

    with dpg.handler_registry():
        dpg.add_mouse_move_handler(callback=self.update_mouse_move)
        dpg.add_mouse_release_handler(callback=self.update_mouse_release)

    # open the welcome window
    switch_window("WELCOME_WINDOW")

    dpg.setup_dearpygui() 
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)

    # set function to execute when window is resized
    dpg.set_viewport_resize_callback(self.update_window_size)
    
    self.update_window_size()

  def switch_to_welcome(self):
    switch_window("WELCOME_WINDOW")

  def switch_to_add_recording(self):
    switch_window("ADD_RECORDING_WINDOW")

  def switch_to_library(self):
    switch_window("LIBRARY_WINDOW")

  def switch_to_tutorial(self):
    switch_window("TUTORIAL_WINDOW")

  def update_window_size(self):
    # if there's an open window with its own resize function, execute here
    global open_window
    if hasattr(open_window, "on_window_resize"):
      open_window.on_window_resize()

  def update_mouse_move(self):
    # if there's an open window with its own mousemove function, execute here
    global open_window
    if hasattr(open_window, "on_mouse_move"):
      open_window.on_mouse_move()

  def update_mouse_release(self):
    # if there's an open window with its own mouserelease function, execute here
    global open_window
    if hasattr(open_window, "on_mouse_release"):
      open_window.on_mouse_release()

  def run(self):
    while dpg.is_dearpygui_running():
      # if there's an open window with its own render_loop function, execute it here
      global open_window
      if hasattr(open_window, "on_render_loop"):
        open_window.on_render_loop()
      dpg.render_dearpygui_frame()
    dpg.destroy_context()

if __name__ == "__main__":
  db = RepertoireDatabase()
  AppManager().run()
