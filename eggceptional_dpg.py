import dearpygui.dearpygui as dpg
import pygame
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
import simpleaudio as sa
import numpy as np
import math
import threading

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

# ID of playback cursor
cursor_id = None

class AudioPlayer:
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
                    with dpg.table(header_row=False, tag="plot_display_table", width=-1):
                        dpg.add_table_column()
            with dpg.child_window(tag="bottom_bar", width=-1, height=50):
                    dpg.add_button(label="Play", tag="play_button", callback=self.toggle_play_pause)
                    dpg.add_text("00:00/00:00", tag="playtime_status_text")
                    dpg.add_button(label="Reset", tag="reset_play_button", callback=self.reset_play)

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

        global loaded_audio
        loaded_audio.clear()
        loaded_audio["file_details"] = app_data
        self.set_is_playing(False)
        loaded_audio["current_time_index"] = 0
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
        loaded_audio["duration"] = duration * 1000
        dur_minutes = self.get_minutes(loaded_audio["duration"])
        dur_seconds = self.get_seconds_remainder(loaded_audio["duration"])
        dpg.set_value("playtime_status_text", f"00:00/{dur_minutes:02d}:{dur_seconds:02d}")
        num_lines = math.ceil(duration / SECONDS_PER_ROW)

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        # Clear previous plots (if any exist)
        dpg.delete_item("plot_display_table", children_only=True)
        dpg.add_table_column(parent="plot_display_table")
        dpg.hide_item("no_file_text")

        # loop over each line and create a plot for each chunk
        for i in range(num_lines):
            # limits of time range per chunk
            min_time = i * SECONDS_PER_ROW
            max_time = min(min_time + SECONDS_PER_ROW, math.floor(duration))
            # if extra audio is <1 second, cut it off
            if (max_time-min_time == 0):
                break

            # Generate X values (time axis)
            time = np.linspace(min_time, max_time, num=(max_time-min_time)*audio.frame_rate)
            chunk_samples = samples[min_time*audio.frame_rate:max_time*audio.frame_rate]

            # container for this line
            if dpg.does_item_exist("plot_display_table"):
                with dpg.table_row(tag=f"display_row{i}", parent="plot_display_table"):
                    # plot the line
                    with dpg.plot(tag=f"Waveform{i}", height=400, width=-1, parent=f"display_row{i}"):
                        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis{i}")
                        y_axis = dpg.add_plot_axis(dpg.mvYAxis, tag=f"y_axis{i}")
                        dpg.add_line_series(time, chunk_samples, label="Audio Signal", parent=y_axis)

                        # fix time and amplitude so that the user can't scroll around
                        dpg.set_axis_limits(f"x_axis{i}", min_time, max_time)
                        dpg.set_axis_limits(f"y_axis{i}", -1, 1)
            else:
                print("Error: Table 'plot_display_table' not found")
                return
        # Initialize cursor
        dpg.delete_item("playback_cursor")
        dpg.add_inf_line_series([0], tag="playback_cursor", label="vertical line", parent="y_axis0")  # vertical line

    # sets loaded_audio["is_playing"] to given value, and updates play button text
    def set_is_playing(self, playing_value):
        global loaded_audio
        if loaded_audio == None:
            return
        loaded_audio["is_playing"] = playing_value
        if playing_value:
            dpg.set_item_label("play_button", "Pause")
        else:
            dpg.set_item_label("play_button", "Play")

    # Toggle play/pause of loaded audio on button click
    def toggle_play_pause(self):
        global loaded_audio
        if loaded_audio == None or loaded_audio["is_playing"] == None:
            return

        # going from play state to pause state
        if loaded_audio["is_playing"]:
            self.set_is_playing(False)
            loaded_audio["current_time_index"] = pygame.mixer.music.get_pos() + loaded_audio["current_time_index"]
            pygame.mixer.music.pause()
        # going from pause state to play state
        else:
            self.set_is_playing(True)
            if loaded_audio["current_time_index"] == None:
                loaded_audio["current_time_index"] = 0
            pygame.mixer.music.load(loaded_audio["file_details"]["file_path_name"])
            pygame.mixer.music.play(start=loaded_audio["current_time_index"]/1000)  # Convert ms to seconds

    # return to timestamp 0 of given audio file
    def reset_play(self):
        global loaded_audio
        if loaded_audio == None:
            return
        self.set_is_playing(False)
        loaded_audio["current_time_index"] = 0
        self.update_position_label()

    def update_window_size(self):
        # keep waveform window above bottom panel
        new_height = dpg.get_viewport_height() - 2.25*BOTTOM_PANEL_HEIGHT
        dpg.set_item_height("waveform_plot", new_height)
        # center play button & playtime text
        screen_center = int(dpg.get_viewport_width() / 2)
        play_button_top = int(BOTTOM_PANEL_HEIGHT / 2 - PLAY_BUTTON_RADIUS)
        #playtime_text_top = play_button_top + PLAY_BUTTON_RADIUS * 2
        dpg.set_item_pos("play_button", [screen_center - PLAY_BUTTON_RADIUS, play_button_top])
        #dpg.set_item_pos("playtime_status_text", [int(screen_center - dpg.get_item_width("playtime_status_text")/2), playtime_text_top])

    def update_position_label(self):
        global loaded_audio
        if loaded_audio:
            if not loaded_audio["is_playing"]:
                pos = loaded_audio["current_time_index"]
            else:
                pos = pygame.mixer.music.get_pos() + loaded_audio["current_time_index"]

            # pos might be a negative value once the playback is completed
            if pos < 0 or pos > loaded_audio["duration"] * 1000:
                self.set_is_playing(False)
                loaded_audio["current_time_index"] = 0
                return
            # ms to s for position
            minutes = self.get_minutes(pos)
            seconds = self.get_seconds_remainder(pos)
            # ms to s for duration
            dur_minutes = self.get_minutes(loaded_audio["duration"])
            dur_seconds = self.get_seconds_remainder(loaded_audio["duration"])
            dpg.set_value("playtime_status_text", f"{minutes:02d}:{seconds:02d}/{dur_minutes:02d}:{dur_seconds:02d}")

    def update_cursor_motion(self):
        global loaded_audio
        if loaded_audio:
            if not loaded_audio["is_playing"]:
                pos = loaded_audio["current_time_index"] / 1000
            else:
                pos = (pygame.mixer.music.get_pos() + loaded_audio["current_time_index"]) / 1000
        else:
            return
        if pos > 0 and pos <= loaded_audio["duration"]:
            row_number = pos // SECONDS_PER_ROW
            # base cursor parent (row) on the seconds per row
            new_cursor_parent = f"y_axis{row_number}"
            dpg.set_value("playback_cursor", [[pos % SECONDS_PER_ROW]])
            #dpg.set_parent("playback_cursor", new_cursor_parent)

    def update_callback(self):
        global loaded_audio
        if loaded_audio and "is_playing" in loaded_audio and loaded_audio["is_playing"]:
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