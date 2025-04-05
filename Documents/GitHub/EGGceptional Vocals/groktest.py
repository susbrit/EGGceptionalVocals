import dearpygui.dearpygui as dpg
import pygame

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.audio_file = None
        self.is_playing = False
        self.paused_time = 0
        
        # Initialize DPG
        dpg.create_context()
        dpg.create_viewport(title="Audio Player", width=400, height=300)
        
        with dpg.window(label="Audio Player", tag="primary_window"):
            # File selection button
            dpg.add_button(label="Select Audio File", callback=self.select_file)
            
            # Child window containing the table
            with dpg.child_window(tag="waveform_plot", width=-1, height=-1):
                dpg.add_text("No file selected. Please load an audio file.", tag="status_text")
                with dpg.table(header_row=False, tag="plot_display_table", width=-1):
                    dpg.add_table_column()  # For controls
                    dpg.add_table_column()  # For status
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
    
    def select_file(self, sender, app_data):
        with dpg.file_dialog(callback=self.audio_file_selected, file_count=1, modal=True):
            dpg.add_file_extension(".mp3")
            dpg.add_file_extension(".wav")
    
    def audio_file_selected(self, sender, app_data):
        self.audio_file = app_data["selections"][list(app_data["selections"].keys())[0]]
        
        # Clear existing rows if any
        if dpg.does_item_exist("plot_display_table"):
            children = dpg.get_item_children("plot_display_table")[1]  # 1 for rows
            for child in children:
                dpg.delete_item(child)
            
            # Add new row with explicit parent
            with dpg.table_row(parent="plot_display_table"):
                dpg.add_button(label="Play", callback=self.toggle_play_pause, tag="play_button")
                dpg.add_text(f"File: {self.audio_file.split('/')[-1]}")
            
            # Update status text
            dpg.configure_item("status_text", show=False)
        else:
            print("Error: Table 'plot_display_table' not found")
    
    def toggle_play_pause(self, sender, app_data):
        if not self.audio_file:
            return
        
        if self.is_playing:
            self.paused_time = pygame.mixer.music.get_pos() / 1000
            pygame.mixer.music.pause()
            self.is_playing = False
            dpg.configure_item("play_button", label="Play")
        else:
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play(start=self.paused_time)
            self.is_playing = True
            dpg.configure_item("play_button", label="Pause")
    
    def run(self):
        dpg.start_dearpygui()
        dpg.destroy_context()

if __name__ == "__main__":
    player = AudioPlayer()
    player.run()