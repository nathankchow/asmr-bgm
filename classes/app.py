'''
EXAMPLES
# defining the callback function (observer)
def my_callback(var, indx, mode):
    print ("Traced variable {}".format(my_var.get())

BUGS
when song replays, will start from last place clicked, as opposed from the begining

NOTES
wav position seeking is impossible (pygame limitation)


TODO
add labels for mimikaki and bgm songs
add buttons for clearing mimikaki and bgm songs 
add a mute checkbox 
add an option for processing ASMR files separately 
properly arrage the widgets on window 
rewrite select asmr + select bgm functions, adding log as needed 
rewrite song playing functionality  
do experiments + remove audio mixing bugs 
'''

import tkinter.filedialog
import tkinter.ttk as ttk 
import tkinter as tk
import pygame
import os
import time

from pathlib import Path 
from classes.writer import Writer
from classes.messages import Messages
from functools import partial 
import threading 

class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("640x580")
        self.window.minsize(640,580)
        self.window.title("asmr-bgm-gui")
        pygame.init()
        pygame.mixer.init()
        self.bgmpath = ''
        self.asmrpath = ''
        self.new_scale_position = 0 
        self.writer = Writer()
        self.messages = Messages(self)
        self.mixing_bool = False
        self.mixing_queue = [] 
        self.fasp = False #freeze auto song position, for when user is clicking on seeking slider 

        self.create_widgets()
        self.post('Welcome to asmr-bgm-gui.')
        

    def create_widgets(self):
        self.mix_button = tk.Button(self.window, text="Mix!", command = self.Mix)
        self.mix_button.pack(fill="x")
        
        self.select_asmr_track_button = tk.Button(self.window, text="Select ASMR track", command = self.Select_asmr_track)
        self.select_bgm_track_button = tk.Button(self.window, text="Select BGM track", command = self.Select_bgm_track)
        self.exit_button = tk.Button(self.window,text="Exit",command=self.window.quit)

        self.asmr_volume_label = tk.Label(self.window, text = "ASMR Volume")
        self.asmr_volume_scale = tk.Scale(self.window,from_=0.0,to_=100.0, orient = tk.HORIZONTAL, resolution = 1, command=self.Asmr_volume)
        self.asmr_volume_scale.set(20)

        self.bgm_volume_label = tk.Label(self.window, text = "BGM Volume")
        self.bgm_volume_scale = tk.Scale(self.window,from_=0.0,to_=100.0, orient = tk.HORIZONTAL, resolution = 1, command=self.Bgm_volume)
        self.bgm_volume_scale.set(20)
        
        self.song_position_scale = tk.Scale(self.window,from_=0, to_=1, orient=tk.HORIZONTAL, resolution = 0.0001, showvalue=False)
        self.song_position_scale.bind('<ButtonPress>',self.Freeze_auto_song_position)
        self.song_position_scale.bind('<ButtonRelease>', self.Song_position_manual)
        self.s1 = tk.StringVar(self.window, "00:00:00 / 00:00:00")
        self.duration_label = tk.Label(self.window,text=self.s1.get())
        self.duration_label.pack()
        self.song_position_label = tk.Label(self.window, text='')

        

        self.song_position_scale.pack(fill="x")

        self.song_position_label.pack()
        self.asmr_volume_label.pack()
        self.asmr_volume_scale.pack(fill="x")
        self.bgm_volume_label.pack()
        self.bgm_volume_scale.pack(fill="x")
        self.select_asmr_track_button.pack(fill="x")
        self.select_bgm_track_button.pack(fill="x")

        self.c1v = tk.BooleanVar(self.window,False)
        self.c1 = tk.Checkbutton(self.window, text='Add loaded audio tracks to library directory', variable=self.c1v)
        self.c1.pack(fill='x')

        self.c2v = tk.BooleanVar(self.window,False)
        self.c2 = tk.Checkbutton(self.window, text='Manually set output directory', variable=self.c2v)
        self.c2.pack(fill='x')

        self.c3v = tk.BooleanVar(self.window,False)
        self.c3 = tk.Checkbutton(self.window, text='Manually set output file name', variable=self.c3v)
        self.c3.pack(fill='x')

        self.log = tk.Label(self.window, text=self.messages.get(), justify=tk.LEFT, anchor='w')
        self.log.pack(fill='x')
        
        tk.Button(self.window,text='↑',command=self.up).pack()
        tk.Button(self.window,text='↓',command=self.down).pack()

        self.exit_button.pack(fill='x')

        self.debug_b = tk.Button(self.window, text='debug',command=self.debug).pack()

        self.s1.trace('w',self.update)

    def update(*args):
        print(args)
        self = args[0]
        self.duration_label.config(text=self.s1.get())

    def logupdate(*args):
        print(args)
        self = args[0]
        self.log.config(text=self.messages.get())
    
    def up(self):
        self.messages.up()
        self.log.config(text=self.messages.get())

    def down(self):
        self.messages.down()
        self.log.config(text=self.messages.get())

    def debug(self):
        self.post('fefefefefwfa')
        self.log.config(text=self.messages.get())

    def msg_up(self):
        pass

    def msg_down(self):
        pass

    def Mix(self): #with threading 
        if self.Assert_both_tracks:
            x = threading.Thread(target=self.writer.mix,args = (
                self.asmrpath,
                self.bgmpath,
                self.asmr_volume_scale.get(),
                self.bgm_volume_scale.get()
                ), daemon=True)
            x.start()

    def Asmr_volume(self, other): 
        if App.Assert_both_tracks(self):
            pygame.mixer.music.set_volume(self.asmr_volume_scale.get()/100)
            
    def Bgm_volume(self, other):
        if App.Assert_both_tracks(self):
            self.bgm_track.set_volume(self.bgm_volume_scale.get()/100)
            
    def Select_asmr_track(self):
        self.asmrpath = tk.filedialog.askopenfilenames()
        print(f'{self.asmrpath} was selected, type is {type(self.asmrpath)}')
        if len(self.asmrpath) == 1 and type(self.asmrpath) == tuple:
            self.asmrpath = self.asmrpath[0] #unpack tuple 
        elif type(self.asmrpath) != tuple:
            pass
        elif len(self.asmrpath) != 1 and type(self.asmrpath) == tuple:
            #multiple files specified, concatenate them and store result in temp 
            print('Concatenating files...')
            self.asmrpath = self.writer.concatenate(self.asmrpath)

        print('Loading ASMR track...')
        pygame.mixer.music.load(self.asmrpath)
        print('ASMR track loaded.')
        self.asmr_track_length = self.writer.getDuration(self.asmrpath)
        print(self.asmr_track_length)



        if self.Assert_both_tracks(self):
            print('Playing audio...') ###   
            self.Audio_play()


    def Select_bgm_track(self):

        self.bgmpath = tk.filedialog.askopenfilename()
        try:
            self.bgm_track.stop()
        except:
            pass
        print('Loading BGM track...') ###
        self.bgm_track = pygame.mixer.Sound(self.bgmpath)
        print('BGM track loaded.')

        if self.Assert_both_tracks(self):
            print('Playing audio...') ###
            self.Audio_play()

    def Assert_both_tracks(*args):
        #Return true if both tracks are loaded, and false if not
        self = args[0]
        if self.bgmpath != '' and self.asmrpath != '':
            return True
        else:
            return False

    def Audio_play(self):
        pygame.mixer.music.play(0)
        self.bgm_track.play(-1)
        self.Asmr_volume('dummy-event')
        self.Bgm_volume('dummy-event')
        self.Song_position_auto()
        
    
    def Song_position_auto(*args): #stopped music starts when position is moved 
        self = args[0]
        #print('expected', round(pygame.mixer.music.get_pos())) #debugging statement
        #print(pygame.mixer.music.get_busy())
        if self.fasp == True:
            self.window.after(500, self.Song_position_auto)
        elif self.fasp == False: 
            if pygame.mixer.music.get_busy():
                self.song_position_scale.set(round(pygame.mixer.music.get_pos()/1000 /self.asmr_track_length,4) + self.new_scale_position)
                self.window.after(500, self.Song_position_auto)
            elif not pygame.mixer.music.get_busy(): #either asmr isn't loaded or manual song position was set
                if self.asmrpath == '':
                    pass
                else: 
                #print(int(self.song_position_scale.get() * self.asmr_track_length))//
                    print('song ended i guess?')
                    print(self.song_position_scale.get())
                    self.song_position_scale.set(0)
                    print(self.song_position_scale.get())
                    pygame.mixer.music.play(start = int(self.song_position_scale.get() * self.asmr_track_length))
                    self.new_scale_position = 0 
                    self.window.after(500, self.Song_position_auto)
        self.s1.set(f'{self.hhmmss(int(self.song_position_scale.get() * self.asmr_track_length))} / {self.hhmmss(self.asmr_track_length)}')

    def Song_position_manual(self,event):
        self.new_scale_position = self.song_position_scale.get()
        #pygame.mixer.music.stop() 
        pygame.mixer.music.play(start = int(self.song_position_scale.get() * self.asmr_track_length))
        self.fasp = False #re-enable auto-songposition after mouse button release event is detected
        self.s1.set(f'{self.hhmmss(int(self.song_position_scale.get() * self.asmr_track_length))} / {self.hhmmss(self.asmr_track_length)}')

    def Freeze_auto_song_position(self,event):
        self.fasp = True

    def post(self,msg):
        self.messages.post(f'{time.strftime("%H:%M:%S", time.localtime())}: {msg}')
        self.log.config(text=self.messages.get())

    def hhmmss(self,seconds):
        return time.strftime('%H:%M:%S', time.gmtime(seconds))


    