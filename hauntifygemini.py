import tkinter as tk
from tkinter import filedialog
from tkinter import *
import pygame
import os
import sys
import random,time
from time import sleep

def set_volume(val):
    """ Sets the volume of the music mixer. """
    volume = int(val) / 100
    pygame.mixer.music.set_volume(volume)

def set_song_position(val):
    """ Sets the playback position of the song. """
    if picked_music and pygame.mixer.music.get_busy():
        new_pos = int(val)
        pygame.mixer.music.set_pos(new_pos)

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

# The resize_widgets function is no longer needed as the new grid layout handles scaling.

pygame.init()
SONG_END = pygame.USEREVENT+1
root = Tk()
root.title('Hauntify Pre-Release Testing Version 0.0.0.11')
root.resizable(True, True)
# root.iconbitmap('icons/logo.ico')

path = ""
pygame.mixer.init()
dicts = []
songs = []
current_song = ""
paused = False
picked_music = False
shuffling = False
current_song_length = 0

# Define a custom border color to use throughout the app
border_color = '#5A4286'

# Get the path to the executable's directory for a consistent config file location
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Use the application path to define the config file path
config_file_path = os.path.join(application_path, ".last_dir.txt")

def shuffle(x):
    """ This is the custom shuffle method. It sorts a list based on a randomly generated key for each item. """
    
    # Create a list of dictionaries where each dictionary contains the original item and a random sort key
    shuffled_with_keys = [
        {"original": item, "sort_key": random.randint(0, 1000)}
        for item in x
    ]
    
    # Sort the list of dictionaries based on the random sort key
    shuffled_with_keys.sort(key=lambda d: d["sort_key"])
    
    # Return a new list containing only the original items in their new, shuffled order
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
            if(f.endswith(".mp3") or f.endswith(".ogg")):
                songs.append(f)
                dicts.append(dict(key=f, value=os.path.join(root_dir, f)))
    
    # Strip file extensions for display in the listbox
    display_songs = []
    for song in songs:
        title_to_display = song
        if title_to_display.endswith(".mp3"):
            title_to_display = title_to_display[:-4]
        elif title_to_display.endswith(".ogg"):
            title_to_display = title_to_display[:-4]
        display_songs.append(title_to_display)

    for song in display_songs:
        songlist.insert("end", song)
        
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
    global current_song, paused, current_song_length
    if not paused:
        full_path = [i for i in dicts if i["key"]==current_song][0]["value"]
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(SONG_END)
        songlist.selection_clear(0, "end")
        songlist.selection_set(songs.index(current_song))
        
        # Remove file extension from the song title
        title_to_display = current_song
        if title_to_display.endswith(".mp3"):
            title_to_display = title_to_display[:-4]
        elif title_to_display.endswith(".ogg"):
            title_to_display = title_to_display[:-4]
        
        song_title_label.config(text=title_to_display)
        
        # Get song length using Pygame's built-in function
        try:
            from mutagen.mp3 import MP3
            audio = MP3(full_path)
            current_song_length = audio.info.length
        except:
            current_song_length = 0
            
        progress_bar.config(to=current_song_length)
        
        # Update total time label
        minutes = int(current_song_length // 60)
        seconds = int(current_song_length % 60)
        total_time_label.config(text=f"{minutes:02}:{seconds:02}")
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
    global songs, shuffling, current_song
    shuffling = True
    songs = shuffle(songs)
    
    # Update the listbox to reflect the new order
    songlist.delete(0, "end")
    for song in songs:
        title_to_display = song
        if title_to_display.endswith(".mp3"):
            title_to_display = title_to_display[:-4]
        elif title_to_display.endswith(".ogg"):
            title_to_display = title_to_display[:-4]
        songlist.insert("end", title_to_display)

    current_song = songs[0]
    songlist.selection_set(0)
    play_music()
    
def play_selected_music(event):
    """ Play the selected song from the listbox. """
    global current_song
    selected_index = songlist.curselection()
    if selected_index:
        current_song = songs[selected_index[0]]
        play_music()

# The Menu widget now has its own background and foreground color
menubar = Menu(root, bg="#1a0129", fg="#ffffff")
root.config(menu=menubar, bg="#1a0129")
organize_menu = Menu(menubar, tearoff=False, bg="#1a0129", fg="#ffffff")
organize_menu.add_command(label='Select Folder',command=open_folder_dialog)
menubar.add_cascade(label="Add Songs", menu=organize_menu)

# Set up the main grid for the application
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# Create a frame for the playlist and place it in the top half
playlist_frame = Frame(root, bg=root['bg'])
playlist_frame.grid(row=0, column=0, sticky='nsew')
playlist_frame.grid_columnconfigure(0, weight=1)
playlist_frame.grid_rowconfigure(0, weight=0) # For song title
playlist_frame.grid_rowconfigure(1, weight=1) # For playlist listbox

# Song title label
song_title_label = Label(playlist_frame, text="No song playing", bg="#1a0129", fg="#ffffff", font=("Helvetica", 14))
song_title_label.grid(row=0, column=0, pady=(10, 0))

# Updated Listbox with flat borders
songlist = Listbox(
    playlist_frame,
    bg="black",
    fg="#ffffff",
    relief=FLAT,
    bd=0,
    highlightthickness=2,
    highlightbackground=border_color
)
songlist.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
songlist.bind("<Double-Button-1>", play_selected_music)


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


# Use initial sized images for button creation
play_btn = Button(
    control_frame,
    image=play_image,
    bg="#1a0129",
    relief=FLAT,
    bd=0,
    highlightthickness=2,
    highlightbackground=border_color,
    command=play_music
)
shuffle_btn = Button(
    control_frame,
    image=shuffle_image,
    bg="#1a0129",
    relief=FLAT,
    bd=0,
    highlightthickness=2,
    highlightbackground=border_color,
    command=shuffle_music
)
skip_btn = Button(
    control_frame,
    image=skip_image,
    bg="#1a0129",
    relief=FLAT,
    bd=0,
    highlightthickness=2,
    highlightbackground=border_color,
    command=skip_music
)
back_btn = Button(
    control_frame,
    image=back_image,
    bg="#1a0129",
    relief=FLAT,
    bd=0,
    highlightthickness=2,
    highlightbackground=border_color,
    command=back_music
)
pause_btn = Button(
    control_frame,
    image=pause_image,
    bg="#1a0129",
    relief=FLAT,
    bd=0,
    highlightthickness=2,
    highlightbackground=border_color,
    command=pause_music
)

# Use a grid layout for the buttons
play_btn.grid(row=0, column=0, padx=7, pady=2, sticky='nsew')
pause_btn.grid(row=0, column=1, padx=7, pady=2, sticky='nsew')
back_btn.grid(row=0, column=2, padx=7, pady=2, sticky='nsew')
skip_btn.grid(row=0, column=3, padx=7, pady=2, sticky='nsew')
shuffle_btn.grid(row=0, column=4, padx=7, pady=2, sticky='nsew')

# New frame for progress and volume sliders
slider_frame = Frame(controls_frame, bg=controls_frame['bg'])
slider_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=5)
slider_frame.grid_columnconfigure(0, weight=1)
slider_frame.grid_columnconfigure(1, weight=1)
slider_frame.grid_columnconfigure(2, weight=1)

# Progress bar
current_time_label = Label(slider_frame, text="00:00", bg=controls_frame['bg'], fg="#ffffff")
current_time_label.grid(row=0, column=0, sticky='w')

progress_bar = Scale(
    slider_frame,
    from_=0,
    to=100,
    orient=HORIZONTAL,
    bg="#1a0129",
    fg="#5A4286",
    troughcolor="#5A4286",
    relief=FLAT,
    bd=0,
    highlightthickness=0,
    showvalue=False
)
progress_bar.grid(row=0, column=1, sticky='ew')

total_time_label = Label(slider_frame, text="00:00", bg=controls_frame['bg'], fg="#ffffff")
total_time_label.grid(row=0, column=2, sticky='e')

# Volume slider
volume_slider = Scale(
    controls_frame,
    from_=0,
    to=100,
    orient=HORIZONTAL,
    label="Volume",
    bg="#1a0129",
    fg="#5A4286",
    troughcolor="#5A4286",
    relief=FLAT,
    bd=0,
    highlightthickness=0,
    command=set_volume
)
volume_slider.set(50) # Set default volume to 50
volume_slider.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)

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
