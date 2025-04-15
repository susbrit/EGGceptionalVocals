import dearpygui.dearpygui as dpg
import pygame
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
import simpleaudio as sa
import numpy as np
import math
import pandas as pd
import sqlite3

open_window = None
defined_windows = ["PLAYBACK_WINDOW", "WELCOME_WINDOW", "LIBRARY_WINDOW"]

# switch from open_window to window "switching_to"
# where "switching_to" is a string from global array defined_windows
def switch_window(switching_to):
  global open_window
  global defined_windows
  if switching_to not in defined_windows:
    print(f"ERROR: window f{switching_to} does not exist!")
    return

  # first, close existing window
  # switching_from may equal None on app initialization
  if open_window != None:
    try:
      open_window.hide()
    except:
      print("ERROR: could not hide open window?")

  # now open new window
  new_window = None
  try:
    if switching_to == "PLAYBACK_WINDOW":
      new_window = AudioPlayer()
    elif switching_to == "WELCOME_WINDOW":
      new_window = WelcomeScreen()
    elif switching_to == "LIBRARY_WINDOW":
      new_window = LibraryWindow()
  except:
    print(f"ERROR: we don't like switching to ")
  
  open_window = new_window

class AudioPlayer:
  # CONSTANTS
  SECONDS_PER_ROW = 10
  BOTTOM_PANEL_HEIGHT = 60
  PLAY_BUTTON_RADIUS = 20

  # global value for tracking loaded audio
  loaded_audio = dict()
  """
  loaded_audio = {
      "file_details",
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
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.audio_file_selected, id="audio_file_dialog", width=700 ,height=400):
            dpg.add_file_extension("Source files (*.mp3 *.wav){.mp3,.wav}", color=(0, 255, 255, 255))
        dpg.add_button(label="File Selector", callback=lambda: dpg.show_item("audio_file_dialog"))
        dpg.add_text(default_value="", tag="selected_file_name")
        with dpg.child_window(tag="waveform_plot", width=-1):
            dpg.add_text("No file selected. Please load an audio file.", tag="no_file_text")
            with dpg.table(header_row=False, tag="plot_display_table", width=-1, borders_innerH=True):
                dpg.add_table_column()

        with dpg.child_window(tag="bottom_bar", width=-1, height=50):
            dpg.add_button(label="Play", tag="play_button", callback=self.toggle_play_pause)
            dpg.add_text("00:00/00:00", tag="playtime_status_text")
            dpg.add_button(label="Reset", tag="reset_play_button", callback=self.reset_play)
        dpg.add_button(label="Back to Menu", callback=self.back_to_menu)

    with dpg.theme() as self.cursor_red:
        with dpg.theme_component():
            dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 0, 0, 255), category=dpg.mvThemeCat_Plots)

    with dpg.theme() as self.cursor_gray:
        with dpg.theme_component():
            dpg.add_theme_color(dpg.mvPlotCol_Line, (100, 100, 100, 255), category=dpg.mvThemeCat_Plots)

  # TEMP FUNCTION
  def back_to_menu(self):
    switch_window("WELCOME_WINDOW")

  def hide(self):
    pygame.mixer.quit()
    dpg.delete_item("Audio Player Window")

  # event-triggered functions, to be called by AppManager
  def on_render_loop(self):
    if self.loaded_audio and "is_playing" in self.loaded_audio and self.loaded_audio["is_playing"]:
      self.update_position_label()
      self.update_cursor_motion()

  def on_window_resize(self):
    # keep waveform window above bottom panel
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
    if self.loaded_audio:
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
              dpg.set_y_scroll("waveform_plot", dpg.get_y_scroll("waveform_plot")+650) #TEMP hardcoded for demo
          # update position of all cursors
          for cursor_id in self.plot_cursors:
              dpg.set_value(cursor_id, [[pos]])

  # on mousemove, if hovering over a plot, create a new cursor at position
  def update_hover_cursor(self):
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
    # mouse is not on the plot
    if len(self.hover_cursors) == 0:
        return
    x_pos = dpg.get_value(self.hover_cursors[0])[0][0]
    # use the name of the cursor tag to extract the row number to jump to
    row_num = int(self.hover_cursors[0].split('_')[2])
    self.create_cursor_set(row_num, x_pos)
    self.loaded_audio["current_time_index"] = x_pos * 1000
    self.update_position_label()
    self.set_is_playing(False)

  # generates visual of waveform for the selected audio file
  # splits waveform into separate rows if necessary (based on SECONDS_PER_ROW)
  def audio_file_selected(self, sender, app_data):
      if not app_data["file_path_name"]:
          return

      self.plot_cursors.clear()
      self.hover_cursors.clear()
      self.rows_in_table = 0
      self.plots_per_row = 0
      self.loaded_audio.clear()
      self.loaded_audio["file_details"] = app_data
      self.loaded_audio["current_time_index"] = 0
      self.set_is_playing(False)
      # Generate label with audio file name
      dpg.set_value("selected_file_name", app_data["file_name"])

      # Load the audio file
      audio = AudioSegment.from_file(app_data["file_path_name"])
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

      # process input CQ spreadsheet
      cq_file = pd.read_excel('unknown_test_cq.xlsx')
      cq_time = np.array(cq_file.iloc[:, 0].tolist())
      cq_values = np.array(cq_file.iloc[:, 1].tolist())

      if pygame.mixer.music.get_busy():
          pygame.mixer.music.stop()

      # Clear previous plots (if any exist)
      dpg.delete_item("plot_display_table", children_only=True)
      dpg.add_table_column(parent="plot_display_table")
      dpg.hide_item("no_file_text")

      self.plots_per_row = 2 # TEMP hard coded for demo
      self.rows_in_table = num_lines

      # loop over each line and create a plot for each chunk
      for i in range(self.rows_in_table):
          # limits of time range per chunk
          min_time = i * self.SECONDS_PER_ROW
          max_time = min(min_time + self.SECONDS_PER_ROW, math.floor(duration))
          # if extra audio is <1 second, cut it off
          if (max_time-min_time == 0):
              self.rows_in_table = self.rows_in_table - 1
              break
          
          # Generate time values for the CQ values
          time_mask = (cq_time >= min_time) & (cq_time <= max_time)
          cq_time_chunk = cq_time[time_mask]
          cq_value_chunk = cq_values[time_mask]

          # Generate X values for audio data (time axis)
          time = np.linspace(min_time, max_time, num=(max_time-min_time)*audio.frame_rate)
          chunk_samples_audio = samples[min_time*audio.frame_rate:max_time*audio.frame_rate]

          # container for this line
          if dpg.does_item_exist("plot_display_table"):
              with dpg.table_row(tag=f"display_row_{i}", parent="plot_display_table", height=650):
                  with dpg.group(horizontal=False):
                      # TODO: allow user to select what types of data they want displayed on this page
                      # making it dynamic created a glitch, I think due to having a loop within a "with" block
                      # TODO: find another way to make more dynamic without a for loop (eg: always creating each plot, but setting visibility)

                      # plot the waveforms
                      with dpg.plot(tag=f"waveform_{i}_0", height=300, width=-1):
                          x_axis = dpg.add_plot_axis(dpg.mvXAxis, tag=f"x_axis_{i}_0")
                          y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Closed Quotient", tag=f"y_axis_{i}_0")
                          #dpg.add_line_series(time, .5*np.sin(5*time), label="Arbitrary Data", parent=y_axis)
                          dpg.add_line_series(cq_time_chunk, cq_value_chunk, label="Closed Quotient", parent=y_axis)
                          # fix time and amplitude so that the user can't scroll around
                          dpg.set_axis_limits(f"x_axis_{i}_0", min_time, max_time)
                          dpg.set_axis_limits(f"y_axis_{i}_0", -1, 1)
                      with dpg.plot(tag=f"waveform_{i}_1", height=300, width=-1):
                          x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{i}_1")
                          y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Audio Signal", tag=f"y_axis_{i}_1")
                          dpg.add_line_series(time, chunk_samples_audio, label="Audio Signal", parent=y_axis)
                          # fix time and amplitude so that the user can't scroll around
                          dpg.set_axis_limits(f"x_axis_{i}_1", min_time, max_time)
                          dpg.set_axis_limits(f"y_axis_{i}_1", -1, 1)

          else:
              print("Error: Table 'plot_display_table' not found")
              return

      self.create_cursor_set(0)
          
  # Where row_num is the row in table where cursor is initialized to
  def create_cursor_set(self, row_num, x_value=0):
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
    self.loaded_audio["is_playing"] = playing_value
    # play music
    if playing_value:
      dpg.set_item_label("play_button", "Pause")
      if self.loaded_audio["current_time_index"] == None:
          self.loaded_audio["current_time_index"] = 0
      pygame.mixer.music.load(self.loaded_audio["file_details"]["file_path_name"])
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

class LibaryWindow:
  def __init__(self):
    with dpg.child_window(tag="Library Window", parent="Primary Window"):
      dpg.add_text("Your Repertoire Library")

  def hide(self):
    dpg.delete_item("Library Window")

class WelcomeScreen:
  def __init__(self):
    with dpg.child_window(label="Welcome", tag="Welcome Window", parent="Primary Window"):
      dpg.add_text("Welcome to EGGceptional Vocals!")
      dpg.add_button(label="Go to Player", callback=self.create_audio_player_window)

  def create_audio_player_window(self):
    if dpg.does_item_exist("Audio Player Window"):
      print("ERROR: we already created an audio player window, but now you're asking for another one...")
      return
    switch_window("PLAYBACK_WINDOW")

  def hide(self):
    dpg.delete_item("Welcome Window")


class AppManager:
  def __init__(self):
    dpg.create_context()
    dpg.create_viewport(title='Test App', width=600, height=400)
    with dpg.window(tag="Primary Window"):
        with dpg.menu_bar():
            with dpg.menu(label="Setup"):
                dpg.add_menu_item(label="Tutorial")
                dpg.add_menu_item(label="Calibration")

            with dpg.menu(label="Record"):
                dpg.add_menu_item(label="CQ Warmup")
                dpg.add_menu_item(label="Repertoire")
            
            dpg.add_menu_item(label="Playback Library")

    with dpg.handler_registry():
        dpg.add_mouse_move_handler(callback=self.update_mouse_move)
        dpg.add_mouse_release_handler(callback=self.update_mouse_release)

    # open the welcome window
    switch_window("WELCOME_WINDOW")

    dpg.setup_dearpygui()  # <- this should not segfault
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)

    # set function to execute when window is resized
    dpg.set_viewport_resize_callback(self.update_window_size)
    
    self.update_window_size()

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
    AppManager().run()