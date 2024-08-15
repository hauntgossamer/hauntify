from tkinter import filedialog
from tkinter import *
import pygame
import os
import random,time
from time import sleep

t = time.time()

def check_music_end():
        for event in pygame.event.get():
                if event.type == SONG_END:
                        # print(f"Song ended, now playing {current_song}")
                        skip_music()
                        play_music()
        root.after(100, check_music_end)

pygame.init()
SONG_END = pygame.USEREVENT+1
root = Tk()
root.title('Hauntify Pre-Release Testing Version 0.0.0.11')
root.geometry('720x500')
path = ""
pygame.mixer.init()

menubar = Menu(root)
root.config(menu=menubar)
dicts = []
songs = []
current_song = ""
paused = False
picked_music = False
click_pick_music = True
shuffling = False

# testlist = [f"test song {i}" for i in range(1, 27)]
def shuffle(x):
    ceiling = random.randint(100, 100*len(x))
#     testlist = [f"test song {i}" for i in range(1, 1000)]
    while ceiling < x.index(x[-1]):
        ceiling = random.randint(100, ceiling)

    procgen = [(dict(key=j, value=k)) for j,k in enumerate([(random.randint(100, ceiling)) for i in x])]
    
#     print(f"Procedural generation of random dictionaries looks like this: {procgen} \n \n")
    new_indexes =  [i["key"] for i in sorted(procgen, key=lambda d: d["value"])]
#     print(f"The list used to reassign indeces looks like this: \n {new_indexes} \n \n")
    new_list_of_dicts = []
    for i in new_indexes:
        new_list_of_dicts.append(dict(key=i, value=x[i]))
#     print(new_list_of_dicts)
    shuffled_list = [i["value"] for i in new_list_of_dicts]
#     print(f"Provided list looked like this: \n {x} \n \n Shuffled list looks like this: \n {shuffled_list} \n")
    return shuffled_list
# shuffle(testlist)
def clicked_pick_music():
        global click_pick_music 
        click_pick_music = True
def load_music():
        global current_song, songs, path, dicts, picked_music, click_pick_music
        
        # root.directory = "/home/idiedonce/Music/testingvlcscript/"
        # print(click_pick_music)
        if (click_pick_music == True) or (len(songs) == 0 and picked_music == False):
                # print("Picking new music for the queue!")
                if len(songs) > 0:
                        songs = []
                        dicts = []
                        pygame.mixer.music.unload()
                        songlist.delete(0, "end")
                        songlist.selection_clear(0, "end")
                picked_music = True
                click_pick_music = False
                path = filedialog.askdirectory()
                for root, dirs, files in os.walk(path):
                        for f in files:
                                if(f.endswith(".mp3") or f.endswith(".ogg")):
                                        songs.append(f)
                                        dicts.append(dict(key=f, value=os.path.join(root, f)))
                #        print(dict(key=f, value=os.path.join(root, f))) 
                for song in songs:
                        songlist.insert("end", song)
                songlist.selection_set(0)
                current_song = songs[songlist.curselection()[0]]
        else:
                # print("No songs were picked")
                for song in songs:
                        songlist.insert("end", song)
        # print(f"Inserted {song}\n")
        # print(dicts)

        play_music()
        # print(f"Songs have successfully loaded and song list looks like this: \n {songs}")
        # print(f"Current selected song is {current_song}")
def play_music():
        global current_song, paused, path

        if not paused:
                pygame.mixer.music.load([i for i in dicts if i["key"]==current_song][0]["value"])
                pygame.mixer.music.play()
                pygame.mixer.music.set_endevent(SONG_END)
                songlist.selection_clear(0, "end")
                songlist.selection_set(songs.index(current_song))
                current_song = songs[songlist.curselection()[0]]
                # print(f"Next song to play is {current_song}")
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
        global songs, shuffle, shuffling, current_song

        shuffling = True
        new_songs = shuffle(songs)
        # print(f"These songs are shuffled:\n {new_songs}\n")  
        pygame.mixer.music.unload()
        songlist.delete(0, "end")
        songlist.selection_clear(0, "end")
        songs = [song for song in new_songs]
        current_song = songs[0]
        songlist.selection_set(songs.index(current_song))
        print("Now playing \n", current_song)
        load_music()
        # print(f"Shuffled songs look like this: \n \n {songs}")

organize_menu = Menu(menubar, tearoff=False)
organize_menu.add_command(label='Select Folder',command=lambda:[clicked_pick_music(), load_music()])
menubar.add_cascade(label="Add Songs", menu=organize_menu) 
songlist = Listbox(root, bg="black", fg="white", width=300, height=20)
songlist.pack()
# load_music()


play_btn_image =     PhotoImage(file="./icons/play.png")
pause_btn_image =    PhotoImage(file="./icons/pause.png")
shuffle_btn_image =  PhotoImage(file="./icons/shuffle.png")
skip_btn_image =     PhotoImage(file="./icons/skip.png")
back_btn_image =     PhotoImage(file="./icons/back.png")

control_frame = Frame(root)
control_frame.pack()

play_btn = Button(control_frame,    image = play_btn_image,    borderwidth=5, bg="white", command=play_music)
shuffle_btn = Button(control_frame, image = shuffle_btn_image, borderwidth=5, bg="white", command=shuffle_music)
skip_btn = Button(control_frame,    image = skip_btn_image,    borderwidth=5, bg="white", command=skip_music)
back_btn = Button(control_frame,    image = back_btn_image,    borderwidth=5, bg="white", command=back_music)
pause_btn = Button(control_frame,   image = pause_btn_image,   borderwidth=5, bg="white", command=pause_music)


play_btn.grid(row=0, column=0, padx=7, pady=2)
shuffle_btn.grid(row=0, column=4, padx=7, pady=2)
skip_btn.grid(row=0, column=3, padx=7, pady=2)
back_btn.grid(row=0, column=2, padx=7, pady=2)
pause_btn.grid(row=0, column=1, padx=7, pady=2)

check_music_end()
root.mainloop()

pygame.quit()