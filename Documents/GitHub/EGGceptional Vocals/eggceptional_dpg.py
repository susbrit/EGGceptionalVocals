import dearpygui.dearpygui as dpg
import pygame
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
import simpleaudio as sa
import numpy as np
import math
import pandas as pd

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
    #number of plots per table row
    plots_per_row = 0
    #array of ids of plot cursors to update
    plot_cursors = []

    def __init__(self):
        pygame.mixer.init()
        dpg.create_context()
        dpg.create_viewport(title='EGGceptional Vocals')

        with dpg.file_dialog(directory_selector=False, show=False, callback=self.audio_file_selected, id="audio_file_dialog", width=700 ,height=400):
            dpg.add_file_extension("Source files (*.mp3 *.wav){.mp3,.wav}", color=(0, 255, 255, 255))

        with dpg.window(tag="Primary Window"):
            with dpg.menu_bar():
                with dpg.menu(label="Setup"):
                    dpg.add_menu_item(label="Tutorial", callback=self.print_me)
                    dpg.add_menu_item(label="Calibration", callback=self.print_me)

                with dpg.menu(label="Record"):
                    dpg.add_menu_item(label="CQ Warmup", callback=self.print_me)
                    dpg.add_menu_item(label="Repertoire", callback=self.print_me)
                
                dpg.add_menu_item(label="Playback Library", callback=self.print_me)

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
        
        #TODO add this to each plot when they are created
        with dpg.item_handler_registry(tag="plot_hover_handler"):
            dpg.add_item_hover_handler(callback=self.update_hover_cursor)
        dpg.set_viewport_resize_callback(self.update_window_size)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)
        self.update_window_size()

    # UTILITIES #
    # given a value in miliseconds, returns the number of minutes
    def get_minutes(self, ms_value):
        return int(ms_value // 60000)

    # given a value in miliseconds, returns the number of seconds in remainder
    # eg: a value that is, in total, 6 minutes 20 seconds will return 20
    def get_seconds_remainder (self, ms_value):
        return int((ms_value % 60000) // 1000)

    def save_callback():
        print("Save Clicked")

    def print_me(self, sender):
        print(f"Menu Item: {sender}")

    # generates visual of waveform for the selected audio file
    # splits waveform into separate rows if necessary (based on SECONDS_PER_ROW)
    def audio_file_selected(self, sender, app_data):
        if not app_data["file_path_name"]:
            return

        self.loaded_audio.clear()
        self.loaded_audio["file_details"] = app_data
        self.set_is_playing(False)
        self.loaded_audio["current_time_index"] = 0
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
        num_lines = math.ceil(duration /self.SECONDS_PER_ROW)

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        # Clear previous plots (if any exist)
        dpg.delete_item("plot_display_table", children_only=True)
        dpg.add_table_column(parent="plot_display_table")
        dpg.hide_item("no_file_text")

        self.plots_per_row = 2 # TEMP hard coded for demo

        # loop over each line and create a plot for each chunk
        for i in range(num_lines):
            # limits of time range per chunk
            min_time = i * self.SECONDS_PER_ROW
            max_time = min(min_time + self.SECONDS_PER_ROW, math.floor(duration))
            # if extra audio is <1 second, cut it off
            if (max_time-min_time == 0):
                break

            # Generate X values (time axis)
            time = np.linspace(min_time, max_time, num=(max_time-min_time)*audio.frame_rate)
            chunk_samples_audio = samples[min_time*audio.frame_rate:max_time*audio.frame_rate]

            # container for this line
            if dpg.does_item_exist("plot_display_table"):
                with dpg.table_row(tag=f"display_row_{i}", parent="plot_display_table", height=650):
                    with dpg.group(horizontal=False):
                        #TODO make this dynamic to the number of waveform plots being added
                        # plot the extra waveform
                        with dpg.plot(tag=f"extra_waveform_{i}", height=300, width=-1):
                            x_axis = dpg.add_plot_axis(dpg.mvXAxis, tag=f"x_axis_{i}_0")
                            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Arbitrary Data", tag=f"y_axis_{i}_0")
                            dpg.add_line_series(time, .5*np.sin(5*time), label="Arbitrary Data", parent=y_axis)

                            # fix time and amplitude so that the user can't scroll around
                            dpg.set_axis_limits(f"x_axis_{i}_0", min_time, max_time)
                            dpg.set_axis_limits(f"y_axis_{i}_0", -1, 1)
                        # plot the audio waveform
                        with dpg.plot(tag=f"audio_waveform_{i}", height=300, width=-1):
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
            
    # Where row_number is the row of the table to initialize this cursor
    def create_cursor_set(self, row_number, x_value=0):
        # Initialize cursor
        for cursor_id in self.plot_cursors:
            dpg.delete_item(cursor_id)
        self.plot_cursors.clear()
        for i in range (self.plots_per_row):
            cursor_tag = f"playback_cursor_{i}"
            dpg.add_inf_line_series([0], tag=cursor_tag, label="vertical line", parent=f"y_axis_{row_number}_{i}")
            self.plot_cursors.append(cursor_tag)
            dpg.set_value(cursor_tag, [[x_value]])

    # sets loaded_audio["is_playing"] to given value, and updates play button text
    def set_is_playing(self, playing_value):
        if self.loaded_audio == None:
            return
        self.loaded_audio["is_playing"] = playing_value
        if playing_value:
            dpg.set_item_label("play_button", "Pause")
        else:
            dpg.set_item_label("play_button", "Play")

    # Toggle play/pause of loaded audio on button click
    def toggle_play_pause(self):
        if self.loaded_audio == None or self.loaded_audio["is_playing"] == None:
            return

        # going from play state to pause state
        if self.loaded_audio["is_playing"]:
            self.set_is_playing(False)
            self.loaded_audio["current_time_index"] = pygame.mixer.music.get_pos() + self.loaded_audio["current_time_index"]
            pygame.mixer.music.pause()
        # going from pause state to play state
        else:
            self.set_is_playing(True)
            if self.loaded_audio["current_time_index"] == None:
                self.loaded_audio["current_time_index"] = 0
            pygame.mixer.music.load(self.loaded_audio["file_details"]["file_path_name"])
            pygame.mixer.music.play(start=self.loaded_audio["current_time_index"]/1000)  # Convert ms to seconds

    # return to timestamp 0 of given audio file
    def reset_play(self):
        if self.loaded_audio == None:
            return
        self.set_is_playing(False)
        self.loaded_audio["current_time_index"] = 0
        self.update_position_label()
        self.create_cursor_set(0)
        dpg.set_y_scroll("waveform_plot", 0)

    def update_window_size(self):
        # keep waveform window above bottom panel
        new_height = dpg.get_viewport_height() - 2.25*self.BOTTOM_PANEL_HEIGHT
        dpg.set_item_height("waveform_plot", new_height)
        # center play button & playtime text
        screen_center = int(dpg.get_viewport_width() / 2)
        play_button_top = int(self.BOTTOM_PANEL_HEIGHT / 2 - self.PLAY_BUTTON_RADIUS)
        #playtime_text_top = play_button_top + PLAY_BUTTON_RADIUS * 2
        dpg.set_item_pos("play_button", [screen_center - self.PLAY_BUTTON_RADIUS, play_button_top])
        #dpg.set_item_pos("playtime_status_text", [int(screen_center - dpg.get_item_width("playtime_status_text")/2), playtime_text_top])

    def update_position_label(self):
        if self.loaded_audio:
            if not self.loaded_audio["is_playing"]:
                pos = self.loaded_audio["current_time_index"]
            else:
                pos = pygame.mixer.music.get_pos() + self.loaded_audio["current_time_index"]

            # pos might be a negative value once the playback is completed
            if pos < 0 or pos > self.loaded_audio["duration"] * 1000:
                self.set_is_playing(False)
                self.loaded_audio["current_time_index"] = 0
                return
            # ms to s for position
            minutes = self.get_minutes(pos)
            seconds = self.get_seconds_remainder(pos)
            # ms to s for duration
            dur_minutes = self.get_minutes(self.loaded_audio["duration"])
            dur_seconds = self.get_seconds_remainder(self.loaded_audio["duration"])
            dpg.set_value("playtime_status_text", f"{minutes:02d}:{seconds:02d}/{dur_minutes:02d}:{dur_seconds:02d}")

    def update_hover_cursor(self, app_data, plot_data):
        print(f"appdata is {app_data}")
        print(f"plot_data is {plot_data}")

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

    def update_callback(self):
        if self.loaded_audio and "is_playing" in self.loaded_audio and self.loaded_audio["is_playing"]:
            self.update_position_label()
            self.update_cursor_motion()


    def run(self):
        while dpg.is_dearpygui_running():
            self.update_callback()
            dpg.render_dearpygui_frame()
        # cleaning up
        pygame.mixer.quit()
        dpg.destroy_context()

if __name__ == "__main__":
    player = AudioPlayer()
    player.run()