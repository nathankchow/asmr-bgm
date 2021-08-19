import tkinter.filedialog
import tkinter.ttk as ttk 
import tkinter as tk
import pygame
import os
import mutagen
from pathlib import Path 
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from classes.mixer import Mixer
from functools import partial 
import threading 

class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("640x480")
        self.window.title("mimikaki-bgm")
        self.create_widgets()
        pygame.init()
        pygame.mixer.init()
        self.bgm_track_path = ''
        self.asmr_track_path = ''
        self.new_scale_position = 0 
        self.mixer = Mixer()
        self.mixing_bool = False
        self.mixing_queue = [] 

    def create_widgets(self):
        self.seek_label = tk.Label(self.window, text = "Seek")
        mix_button = tk.Button(self.window, text="Mix!", command = self.Mix)
        debug_button = tk.Button(self.window, text="Debug", command = self.Debug)
        select_asmr_track_button = tk.Button(self.window, text="Select ASMR track", command = self.Select_asmr_track)
        select_bgm_track_button = tk.Button(self.window, text="Select BGM track", command = self.Select_bgm_track)
        concatenate_button = tk.Button(self.window, text = "Concatenate (pre-processing)", command = self.Concatenate)
        convert_to_mp3_button = tk.Button(self.window, text = "Convert to MP3 (pre-processing)", command = self.Convert_to_mp3)

        self.asmr_volume_label = tk.Label(self.window, text = "Mimikaki Volume")
        self.asmr_volume_scale = tk.Scale(self.window,from_=0.0,to_=1.0, orient = tk.HORIZONTAL, resolution = 0.001, command=self.Asmr_volume)
        self.asmr_volume_scale.set(1)

        self.bgm_volume_label = tk.Label(self.window, text = "BGM Volume")
        self.bgm_volume_scale = tk.Scale(self.window,from_=0.0,to_=1.0, orient = tk.HORIZONTAL, resolution = 0.001, command=self.Bgm_volume)
        self.bgm_volume_scale.set(1)
        
        self.song_position_scale = tk.Scale(self.window,from_=0, to_=1, orient=tk.HORIZONTAL, resolution = 0.001)
        self.song_position_scale.bind('<ButtonRelease>', self.Song_position_manual)
        self.song_position_label = tk.Label(self.window, text='')

        mix_button.pack(fill="x")

        self.song_position_scale.pack(fill="x")

        self.song_position_label.pack()
        self.asmr_volume_label.pack()
        self.asmr_volume_scale.pack(fill="x")
        self.bgm_volume_label.pack()
        self.bgm_volume_scale.pack(fill="x")
        select_asmr_track_button.pack(fill="x")
        select_bgm_track_button.pack(fill="x")
        concatenate_button.pack(fill='x')
        convert_to_mp3_button.pack(fill='x')
        debug_button.pack(fill="both")

    '''
    def Mix(self):
        if self.Assert_both_tracks:
            #get weights from 
            Mixer.mix(
                self.asmr_track_path,
                self.bgm_track_path,
                (self.asmr_volume_scale.get(), self.bgm_volume_scale.get())
            )
    '''

    def Mix(self): #this version uses threading 
        if self.Assert_both_tracks:
            x = threading.Thread(target=self.mixer.mix,args = (
                self.asmr_track_path,
                self.bgm_track_path,
                (self.asmr_volume_scale.get(), self.bgm_volume_scale.get())
                ), daemon=True)
            x.start()

    def Debug(self):
        print(int(pygame.mixer.music.get_pos()/1000))


    def Asmr_volume(self, other): 
        if App.Assert_both_tracks(self):
            pygame.mixer.music.set_volume(self.asmr_volume_scale.get())
            
    def Bgm_volume(self, other):
        if App.Assert_both_tracks(self):
            self.bgm_track.set_volume(self.bgm_volume_scale.get())
            
    def Select_asmr_track(self):
        self.asmr_track_path = tk.filedialog.askopenfilename()
        if self.asmr_track_path != '':
            print('Loading ASMR track...')
            pygame.mixer.music.load(self.asmr_track_path)
            asmrPath = Path(self.asmr_track_path)
            print(asmrPath.suffix) ###
            if asmrPath.suffix == '.mp3':
                mut = MP3(self.asmr_track_path)
            elif asmrPath.suffix == '.wav':
                mut = WAVE(self.asmr_track_path)
            elif asmrPath.suffix == '.flac': 
                mut = FLAC(self.asmr_track_path)
            #mutagen has no support for reading length of .ogg files currently
            self.asmr_track_length = int(mut.info.length) #length of asmr track in seconds 
            print('ASMR track loaded.')
            print(self.asmr_track_length) ###
            
        elif self.asmr_track_path == '':
            self.asmr_track_length = 0 

        if self.Assert_both_tracks(self):
            print('Playing audio...') ###   
            self.Audio_play(self)


    def Select_bgm_track(self):

        self.bgm_track_path = tk.filedialog.askopenfilename()
        try:
            self.bgm_track.stop()
        except:
            pass
        print('Loading BGM track...') ###
        self.bgm_track = pygame.mixer.Sound(self.bgm_track_path)
        print('BGM track loaded.')

        if self.Assert_both_tracks(self):
            print('Playing audio...') ###
            self.Audio_play(self)

    def Assert_both_tracks(*args):
        #Return true if both tracks are loaded, and false if not
        self = args[0]
        if self.bgm_track_path != '' and self.asmr_track_path != '':
            return True
        else:
            return False

    def Audio_play(*args):
        self = args[0]
        self.asmr_volume_scale.set(0.2)
        self.bgm_volume_scale.set(0.2)
        pygame.mixer.music.play(-1)
        self.bgm_track.play(-1)
        self.window.after(1000, self.Song_position_auto)
    
    def Song_position_auto(*args):
        self = args[0]
        #print('expected', round(pygame.mixer.music.get_pos())) #debugging statement
        #print(pygame.mixer.music.get_busy())
        if pygame.mixer.music.get_busy():
            self.song_position_scale.set(round(pygame.mixer.music.get_pos()/1000 /self.asmr_track_length,3) + self.new_scale_position)
            self.window.after(1000, self.Song_position_auto)
        elif not pygame.mixer.music.get_busy():
            #print(int(self.song_position_scale.get() * self.asmr_track_length))//
            pygame.mixer.music.play(start = int(self.song_position_scale.get() * self.asmr_track_length))
            self.window.after(1000, self.Song_position_auto)

    def Song_position_manual(*args):
        self = args[0]
        self.new_scale_position = self.song_position_scale.get()
        pygame.mixer.music.stop()

    def Concatenate(*args):
        self = args[0]
        name_list = tk.filedialog.askopenfilenames()
        name_list_copy = name_list
        Mixer.concatenate_pt1(name_list_copy)
        new_file_name = tk.filedialog.asksaveasfilename(
            defaultextension='.mp3', filetypes=[("MP3 files", '*.mp3')],
            title="Choose filename"
        )
        Mixer.concatenate_pt2(new_file_name)
    
    def Convert_to_mp3(self):
        file_to_convert = tk.filedialog.askopenfilenames()
        Mixer.convert_to_mp3(file_to_convert)


