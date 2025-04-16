import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from music21 import converter, environment, stream

# Set MuseScore path (adjust as needed)
MUSESCORE_PATH = "/Applications/MuseScore 4.app/Contents/MacOS/mscore"
environment.set('musicxmlPath', MUSESCORE_PATH)

class MuseScoreImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("MuseScore Image Viewer")

        # Open File Button
        self.open_button = tk.Button(root, text="Open MuseScore File", command=self.load_musescore)
        self.open_button.pack(pady=10)

        # Canvas to display images
        self.canvas = tk.Canvas(root, bg="white", width=800, height=600)
        self.canvas.pack()

    def load_musescore(self):
        file_path = filedialog.askopenfilename(filetypes=[("MuseScore & MusicXML Files", "*.mscz *.mscx *.musicxml")])
        if not file_path:
            return

        try:
            # Extract music metadata
            measures, time_signatures = self.extract_music_metadata(file_path)

            # Convert the score to PNG using MuseScore CLI
            output_image_path = file_path + ".png"
            os.system(f'"{MUSESCORE_PATH}" "{file_path}" -o "{output_image_path}"')

            # Display the images with metadata
            self.display_split_images(output_image_path, measures, time_signatures)

        except Exception as e:
            print("Error:", e)

    def extract_music_metadata(self, file_path):
        """Extracts measure numbers and time signatures from the score."""
        score = converter.parse(file_path)
        measures = []
        time_signatures = []

        for part in score.parts:  # Iterate through each part
            for measure in part.getElementsByClass(stream.Measure):
                measures.append(measure.number)
                time_signatures.append(measure.getTimeSignatures()[0] if measure.getTimeSignatures() else None)
            break  # Only use the first part for now

        return measures, time_signatures

    def display_split_images(self, image_path, measures, time_signatures):
        img = Image.open(image_path)
        img_width, img_height = img.size

        # Define how many sections to split into (e.g., 3 rows)
        sections = min(3, len(measures))  # Adjust based on measure count
        section_height = img_height // sections

        self.canvas.delete("all")  # Clear previous images
        y_offset = 10  # Initial offset for displaying images

        for i in range(sections):
            cropped_img = img.crop((0, i * section_height, img_width, (i + 1) * section_height))
            img_tk = ImageTk.PhotoImage(cropped_img)

            self.canvas.create_image(400, y_offset, image=img_tk, anchor="n")
            self.root.image = img_tk  # Keep reference to avoid garbage collection
            y_offset += section_height + 20  # Add space between sections

            # Overlay metadata (time signatures)
            if i < len(time_signatures) and time_signatures[i]:
                self.canvas.create_text(100, y_offset - section_height + 10,
                                        text=f"Time Signature: {time_signatures[i].numerator}/{time_signatures[i].denominator}",
                                        fill="blue", font=("Arial", 12, "bold"), anchor="w")

            # Example: Insert text between sections
            if i < sections - 1:
                self.canvas.create_text(400, y_offset, text="--- Additional Information ---", fill="red", font=("Arial", 14, "bold"))
                y_offset += 30

if __name__ == "__main__":
    root = tk.Tk()
    app = MuseScoreImageViewer(root)
    root.mainloop()
