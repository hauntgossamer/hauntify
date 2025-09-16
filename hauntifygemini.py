import tkinter as tk
from tkinter import filedialog
from tkinter import *
import pygame
import os
import sys
import random,time
from time import sleep
from io import BytesIO
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from PIL import Image, ImageTk, ImageDraw, ImageFont

def set_volume(val):
    """ Sets the volume of the music mixer. """
    volume = int(val) / 100
    pygame.mixer.music.set_volume(volume)

# This function is now only for visual updates, not user manipulation
def update_song_progress():
    """ Updates the song progress bar and time label. """
    global current_song_length
    if pygame.mixer.music.get_busy() and current_song_length > 0:
        elapsed_time = pygame.mixer.music.get_pos() / 1000
        progress_bar.set(elapsed_time)
        
        # Format the time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        formatted_time = f"{minutes:02}:{seconds:02}"
        current_time_label.config(text=formatted_time)

    root.after(1000, update_song_progress)

def check_music_end():
    """ Checks for the end of the song and handles playback. """
    global current_song, shuffling, current_song_length
    for event in pygame.event.get():
        if event.type == SONG_END:
            skip_music()
    root.after(100, check_music_end)

# This new function resizes the album art whenever the window size changes.
def resize_album_art(event):
    """ Resizes the album art image to fit the container. """
    global original_album_art_img
    
    # Check if an image is loaded and if the container has a non-zero size.
    if original_album_art_img and event.width > 0 and event.height > 0:
        # Calculate new dimensions while maintaining aspect ratio
        original_width, original_height = original_album_art_img.size
        ratio = min(event.width / original_width, event.height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)

        # Resize the image and update the label
        resized_img = original_album_art_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Use a global reference to prevent garbage collection
        global resized_album_art_image
        resized_album_art_image = ImageTk.PhotoImage(resized_img)
        album_art_label.config(image=resized_album_art_image)

# Helper function to get metadata, making the code cleaner and more reusable.
def get_metadata(full_path):
    """ Reads metadata from a file and returns a dictionary. """
    metadata = {
        'title': os.path.basename(full_path).rsplit('.', 1)[0],
        'artist': "Unknown Artist",
        'album': "Unknown Album",
        'year': "Unknown Year",
        'length': 0,
        'album_art': None
    }
    
    try:
        if full_path.endswith(".mp3"):
            audio = MP3(full_path)
            if audio.tags:
                title_tag = audio.tags.get("TIT2")
                if title_tag:
                    metadata['title'] = str(title_tag[0])
                artist_tag = audio.tags.get("TPE1")
                if artist_tag:
                    metadata['artist'] = str(artist_tag[0])
                album_tag = audio.tags.get("TALB")
                if album_tag:
                    metadata['album'] = str(album_tag[0])
                year_tag = audio.tags.get("TDRL") or audio.tags.get("TDRC")
                if year_tag:
                    metadata['year'] = str(year_tag[0])
                
                album_art_data = audio.tags.get("APIC:")
                if album_art_data:
                    metadata['album_art'] = Image.open(BytesIO(album_art_data.data))
            metadata['length'] = audio.info.length

        elif full_path.endswith(".ogg"):
            audio = OggVorbis(full_path)
            if audio.tags:
                if 'title' in audio.tags:
                    metadata['title'] = audio.tags['title'][0]
                if 'artist' in audio.tags:
                    metadata['artist'] = audio.tags['artist'][0]
                if 'album' in audio.tags:
                    metadata['album'] = audio.tags['album'][0]
                if 'date' in audio.tags:
                    metadata['year'] = audio.tags['date'][0]
            metadata['length'] = audio.info.length

    except Exception as e:
        print(f"Error reading metadata from {full_path}: {e}")
    
    return metadata

pygame.init()
SONG_END = pygame.USEREVENT+1
root = Tk()
root.title('Hauntify Pre-Release Testing Version 0.0.0.11')
root.resizable(True, True)

path = ""
pygame.mixer.init()
dicts = []
songs = []
current_song = ""
paused = False
picked_music = False
shuffling = False
current_song_length = 0
original_album_art_img = None 

# Define a custom border color to use throughout the app
border_color = '#111144'

# Create a placeholder album art image for files with no embedded art.
# This prevents the UI from looking broken.
placeholder_image_size = 150
placeholder_img = Image.new('RGB', (placeholder_image_size, placeholder_image_size), color='#1a0129')
draw = ImageDraw.Draw(placeholder_img)
draw.rectangle([10, 10, placeholder_image_size - 10, placeholder_image_size - 10], outline="#ffffff", width=2)

try:
    text_font = ImageFont.truetype("Arial", 80)
except IOError:
    try:
        text_font = ImageFont.truetype("DejaVuSans", 80)
    except IOError:
        text_font = ImageFont.load_default()

text_to_draw = "🎶"
bbox = draw.textbbox((0, 0), text_to_draw, font=text_font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = (placeholder_image_size - text_width) / 2
text_y = (placeholder_image_size - text_height) / 2
draw.text((text_x, text_y), text_to_draw, fill="#ffffff", font=text_font)

global placeholder_album_art
placeholder_album_art = ImageTk.PhotoImage(placeholder_img)

# Get the path to the executable's directory for a consistent config file location
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Use the application path to define the config file path
config_file_path = os.path.join(application_path, ".last_dir.txt")

def shuffle(x):
    """ This is the custom shuffle method. It sorts a list based on a randomly generated key for each item. """
    shuffled_with_keys = [
        {"original": item, "sort_key": random.randint(0, 1000)}
        for item in x
    ]
    shuffled_with_keys.sort(key=lambda d: d["sort_key"])
    shuffled_list = [item["original"] for item in shuffled_with_keys]
    return shuffled_list

def load_songs_from_path(folder_path):
    """Clears and loads music from the given folder path."""
    global current_song, songs, dicts, picked_music, current_song_length
    
    if len(songs) > 0:
        songs = []
        dicts = []
        pygame.mixer.music.unload()
        songlist.delete(0, "end")
        songlist.selection_clear(0, "end")
    
    picked_music = True
    
    for root_dir, dirs, files in os.walk(folder_path):
        for f in files:
            full_path = os.path.join(root_dir, f)
            if(f.endswith(".mp3") or f.endswith(".ogg")):
                metadata = get_metadata(full_path)
                display_name = metadata['title']
                songs.append(f)
                dicts.append(dict(key=f, value=full_path, display=display_name))
                
    # Sort the dictionary list by display name
    dicts.sort(key=lambda d: d["display"].lower())
    
    # Clear and repopulate the listbox and songs list in the correct order
    songlist.delete(0, "end")
    songs.clear()
    for d in dicts:
        songs.append(d["key"])
        songlist.insert("end", d["display"])

    if songs:
        songlist.selection_set(0)
        current_song = songs[songlist.curselection()[0]]
        play_music()

def open_folder_dialog():
    """Opens a file dialog for the user to select a folder."""
    global config_file_path
    
    # Check for and read the last saved directory
    initial_dir = None
    if os.path.exists(config_file_path):
        with open(config_file_path, "r") as f:
            initial_dir = f.read().strip()
    
    path = filedialog.askdirectory(initialdir=initial_dir)
    
    # If a path is selected, save it and load the music
    if path:
        with open(config_file_path, "w") as f:
            f.write(path)
        load_songs_from_path(path)
    
def play_music():
    global current_song, paused, current_song_length, original_album_art_img
    if not paused:
        
        # Find the dictionary entry for the current song
        song_entry = [i for i in dicts if i["key"] == current_song][0]
        full_path = song_entry["value"]
        
        # Use the helper function to get all metadata at once
        metadata = get_metadata(full_path)
        
        # Load the song in the mixer
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(SONG_END)
        songlist.selection_clear(0, "end")
        songlist.selection_set(songs.index(current_song))
        
        # Update UI with the retrieved metadata
        song_title_label.config(text=metadata['title'])
        artist_label.config(text=metadata['artist'])
        album_label.config(text=metadata['album'])
        year_label.config(text=metadata['year'])
        
        current_song_length = metadata['length']
        progress_bar.config(to=current_song_length)
        
        minutes = int(current_song_length // 60)
        seconds = int(current_song_length % 60)
        total_time_label.config(text=f"{minutes:02}:{seconds:02}")
        
        # Handle album art
        if metadata['album_art']:
            original_album_art_img = metadata['album_art']
        else:
            original_album_art_img = placeholder_img.copy()
        
        # Trigger album art resize
        album_art_label.event_generate('<Configure>', width=album_art_label.winfo_width(), height=album_art_label.winfo_height())
    else:
        pygame.mixer.music.unpause()
        paused = False

def pause_music():
    global paused
    pygame.mixer.music.pause()
    paused = True

def skip_music():
    global current_song, paused, shuffling
    try:
        songlist.selection_clear(0, "end")
        songlist.selection_set(songs.index(current_song) + 1)
        current_song = songs[songlist.curselection()[0]]
        play_music()
    except:
        if shuffling == False:
            songlist.selection_clear(0, "end")
            songlist.selection_set(0)
            current_song = songs[songlist.curselection()[0]]
            play_music()
        else:
            shuffle_music()

def back_music():
    global current_song, paused, shuffling
    try:
        songlist.selection_clear(0, "end")
        songlist.selection_set(songs.index(current_song) - 1)
        current_song = songs[songlist.curselection()[0]]
        play_music()
    except:
        if shuffling == False:
            songlist.selection_clear(0, "end")
            songlist.selection_set("end")
            current_song = songs[-1]
            play_music()
        else:
            shuffle_music()

def shuffle_music():
    global songs, shuffling, current_song, dicts
    shuffling = True
    
    # Shuffle the list of dictionaries
    dicts = shuffle(dicts)
    
    # Update the listbox to reflect the new order
    songlist.delete(0, "end")
    songs.clear()
    for d in dicts:
        songs.append(d["key"])
        songlist.insert("end", d["display"])

    current_song = songs[0]
    songlist.selection_set(0)
    play_music()
    
def play_selected_music(event):
    """ Play the selected song from the listbox. """
    global current_song, songs
    selected_index = songlist.curselection()
    if selected_index:
        current_song = songs[selected_index[0]]
        play_music()

# The Menu widget now has its own background and foreground color
menubar = Menu(root, bg="#1a0129", fg="#ffffff")
root.config(menu=menubar, bg="#1a0129")

# The dropdown menu is now explicitly themed to match the app
organize_menu = Menu(
    menubar,
    tearoff=False,
    bg="#1a0129",
    fg="#ffffff",
    activebackground="#5A4286",
    activeforeground="#ffffff"
)
organize_menu.add_command(label='Select Folder', command=open_folder_dialog)
menubar.add_cascade(label="Add Songs", menu=organize_menu)

# Set up the main grid for the application
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# Create a frame for the playlist and place it in the top half
playlist_frame = Frame(root, bg=root['bg'])
playlist_frame.grid(row=0, column=0, sticky='nsew')
# Configure the playlist frame to have two columns
playlist_frame.grid_columnconfigure(0, weight=3) # Left column (playlist)
playlist_frame.grid_columnconfigure(1, weight=1) # Right column (album art)
playlist_frame.grid_rowconfigure(0, weight=1)

# Updated Listbox with flat borders.
# We've added the `selectbackground` property to change the highlight color of selected items.
songlist = Listbox(
    playlist_frame,
    bg="black",
    fg="#ffffff",
    relief=FLAT,
    bd=0,
    highlightthickness=2,
    highlightbackground=border_color,
    selectbackground=border_color, # New: Changes the background of a selected item
    selectforeground="#ffffff" # New: Ensures the text is readable on the dark background
)
songlist.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
songlist.bind("<Double-Button-1>", play_selected_music)

# Create a sub-frame for the album art and labels to align them correctly on the right
album_art_frame = Frame(playlist_frame, bg=root['bg'])
album_art_frame.grid(row=0, column=1, sticky='nsew')
album_art_frame.grid_rowconfigure(0, weight=1)
album_art_frame.grid_rowconfigure(1, weight=0)
album_art_frame.grid_rowconfigure(2, weight=0)
album_art_frame.grid_rowconfigure(3, weight=0)
album_art_frame.grid_rowconfigure(4, weight=0)
album_art_frame.grid_columnconfigure(0, weight=1)

# Album art label
album_art_label = Label(album_art_frame, bg="#1a0129", relief=FLAT)
album_art_label.grid(row=0, column=0, pady=(10, 0), sticky='s')
album_art_label.bind('<Configure>', resize_album_art)

# Song title label
song_title_label = Label(album_art_frame, text="No song playing", bg="#1a0129", fg="#ffffff", font=("Helvetica", 14))
song_title_label.grid(row=1, column=0, pady=(0, 0))

# Artist label
artist_label = Label(album_art_frame, text="", bg="#1a0129", fg="#aaaaaa", font=("Helvetica", 10))
artist_label.grid(row=2, column=0, pady=(0, 0))

# New labels for album and year
album_label = Label(album_art_frame, text="", bg="#1a0129", fg="#aaaaaa", font=("Helvetica", 10, "italic"))
album_label.grid(row=3, column=0, pady=(0, 0))

year_label = Label(album_art_frame, text="", bg="#1a0129", fg="#aaaaaa", font=("Helvetica", 10, "italic"))
year_label.grid(row=4, column=0, pady=(0, 10), sticky='n')

# Create a frame for all controls and place it in the bottom half
controls_frame = Frame(root, bg=root['bg'])
controls_frame.grid(row=1, column=0, sticky='nsew', pady=(5, 10))
controls_frame.grid_rowconfigure(0, weight=1)
controls_frame.grid_rowconfigure(1, weight=1)
controls_frame.grid_rowconfigure(2, weight=1)
controls_frame.grid_columnconfigure(0, weight=1)


# Updated control frame with flat borders, now inside controls_frame
control_frame = Frame(
    controls_frame,
    bg=controls_frame['bg'],
    relief=FLAT,
    bd=0
)
control_frame.grid(row=0, column=0, sticky='nsew')
control_frame.grid_columnconfigure(0, weight=1)
control_frame.grid_columnconfigure(1, weight=1)
control_frame.grid_columnconfigure(2, weight=1)
control_frame.grid_columnconfigure(3, weight=1)
control_frame.grid_columnconfigure(4, weight=1)

# Use tk.PhotoImage to load images directly
play_image = tk.PhotoImage(file="./icons/play.png")
pause_image = tk.PhotoImage(file="./icons/pause.png")
shuffle_image = tk.PhotoImage(file="./icons/shuffle.png")
skip_image = tk.PhotoImage(file="./icons/skip.png")
back_image = tk.PhotoImage(file="./icons/back.png")


# Use initial sized images for button creation.
# `activebackground` changes the color when the button is pressed.
play_btn = Button(
    control_frame,
    image=play_image,
    bg="#1a0129",
    relief=RAISED,
    bd=2,
    highlightthickness=0,
    highlightbackground=border_color,
    highlightcolor=border_color,
    activebackground="#5A4286",
    command=play_music
)
shuffle_btn = Button(
    control_frame,
    image=shuffle_image,
    bg="#1a0129",
    relief=RAISED,
    bd=2,
    highlightthickness=0,
    highlightbackground=border_color,
    highlightcolor=border_color,
    activebackground="#5A4286",
    command=shuffle_music
)
skip_btn = Button(
    control_frame,
    image=skip_image,
    bg="#1a0129",
    relief=RAISED,
    bd=2,
    highlightthickness=0,
    highlightbackground=border_color,
    highlightcolor=border_color,
    activebackground="#5A4286",
    command=skip_music
)
back_btn = Button(
    control_frame,
    image=back_image,
    bg="#1a0129",
    relief=RAISED,
    bd=2,
    highlightthickness=0,
    highlightbackground=border_color,
    highlightcolor=border_color,
    activebackground="#5A4286",
    command=back_music
)
pause_btn = Button(
    control_frame,
    image=pause_image,
    bg="#1a0129",
    relief=RAISED,
    bd=2,
    highlightthickness=0,
    highlightbackground=border_color,
    highlightcolor=border_color,
    activebackground="#5A4286",
    command=pause_music
)

# Use a grid layout for the buttons
play_btn.grid(row=0, column=0, padx=7, pady=2, sticky='nsew')
pause_btn.grid(row=0, column=1, padx=7, pady=2, sticky='nsew')
back_btn.grid(row=0, column=2, padx=7, pady=2, sticky='nsew')
skip_btn.grid(row=0, column=3, padx=7, pady=2, sticky='nsew')
shuffle_btn.grid(row=0, column=4, padx=7, pady=2, sticky='nsew')

# New frame for all sliders and place it directly under the buttons
slider_frame = Frame(controls_frame, bg=controls_frame['bg'])
slider_frame.grid(row=1, column=0, sticky='nsew', pady=5)
# Make the middle column expandable
slider_frame.grid_columnconfigure(0, weight=0)
slider_frame.grid_columnconfigure(1, weight=1)
slider_frame.grid_columnconfigure(2, weight=0)

# Progress bar with updated colors
current_time_label = Label(slider_frame, text="00:00", bg=controls_frame['bg'], fg="#ffffff")
current_time_label.grid(row=0, column=0, sticky='w')

progress_bar = Scale(
    slider_frame,
    from_=0,
    to=100,
    orient=HORIZONTAL,
    bg="#1a0129",
    fg="#9F7AEA",
    troughcolor="#5A4286",
    sliderrelief=FLAT,
    bd=0,
    highlightthickness=0,
    showvalue=False,
    state=DISABLED
)
progress_bar.grid(row=0, column=1, sticky='ew')

total_time_label = Label(slider_frame, text="00:00", bg=controls_frame['bg'], fg="#ffffff")
total_time_label.grid(row=0, column=2, sticky='e')

# Label for volume slider
volume_label = Label(slider_frame, text="Volume", bg=controls_frame['bg'], fg="#ffffff")
volume_label.grid(row=1, column=1, sticky='ew')

# Volume slider with updated colors
volume_slider = Scale(
    slider_frame,
    from_=0,
    to=100,
    orient=HORIZONTAL,
    bg="#1a0129",
    fg="#9F7AEA",
    troughcolor="#5A4286",
    sliderrelief=FLAT,
    bd=0,
    highlightthickness=0,
    command=set_volume
)
volume_slider.set(50)
volume_slider.grid(row=2, column=1, sticky='ew', pady=(10, 0))

# Load the last folder's music on startup
if os.path.exists(config_file_path):
    with open(config_file_path, "r") as f:
        last_dir = f.read().strip()
        if last_dir and os.path.isdir(last_dir):
            load_songs_from_path(last_dir)
            if songs:
                shuffle_music()

check_music_end()
update_song_progress()
root.mainloop()

pygame.quit()
