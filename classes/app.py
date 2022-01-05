'''
EXAMPLES
# defining the callback function (observer)
def my_callback({self}, var, indx, mode):
    print ("Traced variable {}".format(my_var.get())

BUGS
-if message is too long, will not display properly in log
-log does not update after user input until all code finishes running (blocking), use threads to fix 

NOTES
wav position seeking is impossible (pygame limitation)
check other file types

all buttons:
-mix
asmr select
asmr clear
bgm select
bgm clear
exit 

checkboxes
mute all audio tracks
copy into lib.
manually set output file name
manually set output directory
concatenate asmr files for previewing and mixing 

other: 
native functions

TODO
buttons:
concatenate
convert to common format 


'''

import shutil
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk as ttk 
import tkinter as tk
from tkinterdnd2 import *
import pygame
import os
import sys
import time

from pathlib import Path 
from classes.writer import Writer, WriterQueue, Consumer
from classes.messages import Messages
import threading 


class App:
    def __init__(self):
        self.MIN_X = 640
        self.MIN_Y =470
        self.window = TkinterDnD.Tk()
        self.window.resizable(0,0) # removes windows-native maximize button
        #self.window.geometry("640x500")
        self.window.minsize(self.MIN_X,self.MIN_Y)
        self.window.maxsize(self.MIN_X,self.MIN_Y)
        self.window.title("asmr-bgm-gui")
        pygame.init()
        pygame.mixer.init()

        self.asmr_path = []
        self.bgm_path = []
        self.asmr_pointer = -1
        self.bgm_pointer = -1 
        
        self.new_scale_position = 0 
        self.writer = Writer()
        self.messages = Messages(self)
        self.writer_queue = [] 
        self.writer_busy = False
        self.fasp = False #freeze auto song position, for when user is clicking on seeking slider


        self.writer_queue = WriterQueue()
        self.consumer = Consumer(self.writer_queue)
        self.consumer.start()

        self.create_widgets()
        self.position_widgets()
        self.window_bindings()
        self.enable_dragdrop()
        self.post('Welcome to asmr-bgm-gui.')
        self.post('Windows drag and drop support enabled! Drag files into ASMR or BGM sections!')
        

    def enable_dragdrop(self):
        def asmr_drop(event):
            print('testing>')
            if event.data:
                print(type(event.data))
                files = self.window.tk.splitlist(event.data)
                for f in files:
                    if os.path.exists(f):
                        self.asmr_select(f)         
        def bgm_drop(event):
            print('testing>')
            if event.data:
                print(type(event.data))
                files = self.window.tk.splitlist(event.data)
                for f in files:
                    if os.path.exists(f):
                        self.bgm_select(f)                                  
        self.asmr_frame.drop_target_register(1, DND_TEXT, DND_FILES)
        self.bgm_frame.drop_target_register(1,DND_TEXT, DND_FILES)
        self.asmr_frame.dnd_bind('<<Drop>>', asmr_drop)
        self.bgm_frame.dnd_bind('<<Drop>>', bgm_drop)


    def create_widgets(self):
        self.asmr_bgm_frame = tk.Frame(self.window)
        self.asmr_frame = tk.Frame(self.asmr_bgm_frame,borderwidth=1,relief=tk.RIDGE)
        
        self.bgm_frame = tk.Frame(self.asmr_bgm_frame,borderwidth=1,relief=tk.RIDGE)
        self.asmr_button_frame = tk.Frame(self.asmr_frame)
        self.bgm_button_frame = tk.Frame(self.bgm_frame)
        self.automatic_directory_frame = tk.Frame(self.window)
        self.output_format_frame = tk.Frame(self.window)

        #button initialization + bindings
        self.log_frame = tk.Frame(self.window)
        self.arrow_frame = tk.Frame(self.log_frame)
        self.arrow_frame.columnconfigure(0,weight=1)

        self.mix_button = tk.Button(self.window, text="Mix!", command = self.mix)
        self.batch_mix_button = tk.Button(self.window, text="Batch mix", command = self.batch_mix)
        
        self.duration_str = tk.StringVar(self.window, "00:00:00 / 00:00:00")
        self.duration_str.trace('w',self.update)
        self.duration_label = tk.Label(self.window,text=self.duration_str.get())  

        self.song_position_scale = tk.Scale(self.window,from_=0, to_=1, orient=tk.HORIZONTAL, resolution = 0.0001, showvalue=False)
        self.song_position_scale.bind('<ButtonPress>',self.Freeze_auto_song_position)
        self.song_position_scale.bind('<ButtonRelease>', self.Song_position_manual)
        self.song_position_scale.config(state=tk.DISABLED)

        self.asmr_label = tk.Label(self.asmr_frame, text = "No track", width=int(self.MIN_X/2))
        self.asmr_volume_label = tk.Label(self.asmr_frame, text = "ASMR Volume")
        self.asmr_volume_scale = tk.Scale(self.asmr_frame,from_=0.0,to_=100.0, orient = tk.HORIZONTAL, resolution = 1, command=self.asmr_volume)
        self.asmr_volume_scale.set(20)
        self.asmr_clear_b = tk.Button(self.asmr_button_frame, text = "Clear", command = self.asmr_clear)
        self.asmr_clear_all_button = tk.Button(self.asmr_button_frame, text="Clear all", command=self.asmr_clear_all)
        self.asmr_select_button = tk.Button(self.asmr_button_frame, text="Select ASMR track(s)", command = self.asmr_select)


        self.bgm_label = tk.Label(self.bgm_frame, text = "No track",width=int(self.MIN_X/2))
        self.bgm_volume_label = tk.Label(self.bgm_frame, text = "BGM Volume")
        self.bgm_volume_scale = tk.Scale(self.bgm_frame,from_=0.0,to_=100.0, orient = tk.HORIZONTAL, resolution = 1, command=self.bgm_volume)
        self.bgm_volume_scale.set(20)
        self.bgm_clear_b = tk.Button(self.bgm_button_frame, text = "Clear", command = self.bgm_clear)
        self.bgm_clear_all_button = tk.Button(self.bgm_button_frame, text='Clear All', command=self.bgm_clear_all)
        self.bgm_select_button = tk.Button(self.bgm_button_frame, text="Select BGM track(s)", command = self.bgm_select)
 
        self.mute_allv = tk.BooleanVar(self.window,False)
        self.mute_all = tk.Checkbutton(self.window, text='Mute all audio tracks (Ctrl+M)', variable=self.mute_allv)
        self.mute_allv.trace('w',self.muted)

        self.copyv = tk.BooleanVar(self.window,False)
        self.copy = tk.Checkbutton(self.window, text='Copy loaded audio tracks into library directory', variable=self.copyv)

        self.manualv = tk.BooleanVar(self.window,False)
        self.manual = tk.Checkbutton(self.window, text='Manually set output directory and filename', variable=self.manualv)
        self.manualv.trace('w',self.manual_function)

        self.automatic_directory = tk.StringVar(self.automatic_directory_frame,value='')
        if os.path.isdir(os.path.join(os.getcwd(),'library','output')) == True:
            self.automatic_directory.set(os.path.join(os.getcwd(),'library','output'))
        else:
            self.automatic_directory.set(os.getcwd())
        self.automatic_directory_label = tk.Label(self.automatic_directory_frame, 
            text=self.automatic_directory.get(),
            relief=tk.SUNKEN,
            bg="#C0C0C0",
            justify=tk.LEFT,
            anchor='w'
            ) #turn fg grey only when manual output checkbox is checked
        #self.automatic_directory_label_external = tk.Label(self.window, text="Output directory:")
        self.automatic_directory_change = tk.Button(self.automatic_directory_frame,text="Change automatic output directory")

        self.output_format = tk.StringVar(self.output_format_frame)
        self.output_format_label = tk.Label(self.output_format_frame,text="Output format")
        self.output_format.set("Same as ASMR")
        self.output_format_dropdown = tk.OptionMenu(self.output_format_frame,self.output_format,"Same as ASMR",".mp3",".ogg",".wav",".flac")

        self.log = tk.Label(self.log_frame, text=self.messages.get(), justify=tk.LEFT, anchor='w', relief=tk.SUNKEN, bg="#C0C0C0")
        
        self.upb = tk.Button(self.arrow_frame,text='↑',command=self.up)
        self.downb = tk.Button(self.arrow_frame,text='↓',command=self.down)

        self.exit_button = tk.Button(self.window,text="Exit",command=self.exit)
        #self.exit_button = tk.Button(self.window,text="Exit",command=self.window.quit)
        self.asmr_left_button = tk.Button(self.asmr_button_frame, text = '|◀◀', command = self.asmr_left)
        self.asmr_right_button = tk.Button(self.asmr_button_frame, text = '▶▶|', command = self.asmr_right)
        self.bgm_left_button = tk.Button(self.bgm_button_frame, text = '|◀◀', command = self.bgm_left)
        self.bgm_right_button = tk.Button(self.bgm_button_frame, text = '▶▶|', command = self.bgm_right)

       
    
    def position_widgets(self):

        #packing 
        self.mix_button.pack(fill="x")
        self.batch_mix_button.pack(fill='x')
        self.duration_label.pack()
        self.song_position_scale.pack(fill="x")
        self.asmr_bgm_frame.pack(fill='x') 
        self.asmr_bgm_frame.columnconfigure(0,weight=1)
        self.asmr_bgm_frame.columnconfigure(1,weight=1)
        self.asmr_frame.grid(row=0,column=0,sticky='nsew')
        self.bgm_frame.grid(row=0,column=1,sticky='nsew')
        

        self.asmr_volume_label.pack(fill='x')
        self.asmr_volume_scale.pack(fill='x')

        self.asmr_label.pack(fill='x')
        self.asmr_button_frame.pack(fill='x')
        self.asmr_button_frame.columnconfigure(index=0,weight=1)
        self.asmr_button_frame.columnconfigure(index=1,weight=1)
        self.asmr_button_frame.columnconfigure(index=2,weight=1)
        self.asmr_button_frame.columnconfigure(index=3,weight=1)
        self.asmr_button_frame.columnconfigure(index=4,weight=1)
        self.asmr_left_button.grid(row=0,column=0, sticky="WE")
        self.asmr_select_button.grid(row=0,column=1,sticky="WE") 
        self.asmr_clear_b.grid(row=0,column=2,sticky="WE")
        self.asmr_clear_all_button.grid(row=0,column=3,sticky="WE")
        self.asmr_right_button.grid(row=0,column=4,sticky="WE")

        self.bgm_volume_label.pack(fill='x')
        self.bgm_volume_scale.pack(fill='x')
        self.bgm_label.pack(fill='x')
        self.bgm_button_frame.pack(fill='x')
        self.bgm_button_frame.columnconfigure(index=0,weight=1)
        self.bgm_button_frame.columnconfigure(index=1,weight=1)
        self.bgm_button_frame.columnconfigure(index=2,weight=1)
        self.bgm_button_frame.columnconfigure(index=3,weight=1)
        self.bgm_button_frame.columnconfigure(index=4,weight=1)
        self.bgm_left_button.grid(row=0,column=0, sticky="WE")
        self.bgm_select_button.grid(row=0,column=1,sticky="WE") 
        self.bgm_clear_b.grid(row=0,column=2,sticky="WE")
        self.bgm_clear_all_button.grid(row=0,column=3,sticky="WE")
        self.bgm_right_button.grid(row=0,column=4,sticky="WE")
        
        self.mute_all.pack()
        self.copy.pack()
        self.manual.pack()

        self.output_format_label.pack(side=tk.LEFT)
        self.output_format_dropdown.pack(side=tk.LEFT)
        self.output_format_frame.pack()

        self.automatic_directory_frame.pack(fill='x')
        self.automatic_directory_change.pack(side=tk.RIGHT,padx=4)
        self.automatic_directory_label.pack(fill='both', expand=True)

        self.log_frame.pack(fill='x')
        self.arrow_frame.pack(side = tk.RIGHT, fill='y')
        self.arrow_frame.rowconfigure(0,weight=1)
        self.arrow_frame.rowconfigure(1,weight=1)
        self.upb.grid(row=0,column=0,sticky='nsew')
        self.downb.grid(row=1,column=0,sticky='nsew')
        self.log.pack(fill='x')

        self.exit_button.pack(fill='both',expand=True)
                
    def window_bindings(self):
        #bind keyboard shortcuts to top window
        self.window.bind("<Control-a>", self.asmr_select)
        self.window.bind("<Control-b>", self.bgm_select)
        self.window.bind("<Control-m>", self.mute_hotkey)
        self.window.bind("<Control-h>", self.help)
        self.window.bind("<Control-Return>", self.mix)
        self.window.protocol("WM_DELETE_WINDOW", self.exit)

    def debug(self):
        pass

    def update(self, var, indx, mode):
        self.duration_label.config(text=self.duration_str.get())

    def logupdate(self, var, indx, mode):
        self.log.config(text=self.messages.get())
    
    def up(self):
        self.messages.up()
        self.log.config(text=self.messages.get())

    def down(self):
        self.messages.down()
        self.log.config(text=self.messages.get())

    def mix(self, *others): 
        if len(self.asmr_path) and len(self.bgm_path):
            self.post("Item added to mixing queue.")
            self.writer_queue.put((self.writer.mix,
            (
                self.asmr_path[self.asmr_pointer],
                self.bgm_path[self.bgm_pointer][1],
                self.asmr_volume_scale.get(),
                self.bgm_volume_scale.get(),
                self.output_format.get(),
                self, #pass self as argument to get confirmation message after completion
                )))
        else:
            self.post("Error with mix - please load audio files to be mixed.")

    def batch_mix(self):
        #ask for list of directories
        ans = tk.filedialog.askopenfilenames()
        for file in ans:
            if self.assert_audio_file(file):
                self.writer_queue.put(
                    (self.writer.mix,
                        (
                            file,
                            self.bgm_path[self.bgm_pointer][1],
                            self.asmr_volume_scale.get(),
                            self.bgm_volume_scale.get(),
                            self.output_format.get(),
                            self, #pass self as argument to get confirmation message after completion
                        )      
                    )
                )
    
    def assert_audio_file(self, file): #assert that the audio file is 
        return True

            
    def asmr_volume(self, *args):
        if len(self.asmr_path) != 0: #check that asmr file is loaded
            if self.mute_allv.get(): #check that mute all isn't enabled
                pygame.mixer.music.set_volume(0)
                return 
            else:
                pygame.mixer.music.set_volume(self.asmr_volume_scale.get()/100)
            
    def bgm_volume(self, *args):
        if len(self.bgm_path) != 0:
            if self.mute_allv.get():
                self.bgm_path[self.bgm_pointer][0].set_volume(0)
                return 
            else:
                self.bgm_path[self.bgm_pointer][0].set_volume(self.bgm_volume_scale.get()/100)

    def both_volume(self, *other):
        self.asmr_volume()
        self.bgm_volume()
        
    def asmr_select(self, *others):
        if len(others) == 0:
            ans = tk.filedialog.askopenfilenames()
        else:
            ans = (others[0],)
        if len(ans) == 0: 
            return
        else:
            for file in ans:
                if file.endswith('.wav'):
                    file = self.writer.wav_to_flac(file)
                if self.assert_audio_file(file):
                    self.asmr_path.append(file)
                self.asmr_pointer = len(self.asmr_path) - 1
                if self.copyv == True:
                    self.asmr_copy()
        self.asmr_load()

    def asmr_load(self):
        if len(self.asmr_path) == 0: 
            return
        if self.asmr_pointer < 0:
            self.asmr_pointer = 0 #set pointer to first song if songlist is not empty .')
        track = self.asmr_path[self.asmr_pointer]
        self.new_scale_position = 0 
        pygame.mixer.music.load(track)
        self.asmr_track_length = self.writer.getDuration(track)
        self.asmr_label.config(text=Path(track).stem)

        if self.copyv.get() == True:
            self.asmr_copy()

        self.song_position_scale.config(state=tk.NORMAL)
        self.asmr_play()

    def asmr_play(self):
        pygame.mixer.music.play(0)
        #self.bgm_track.play(-1)
        self.asmr_volume('dummy-event')
        #self.bgm_volume('dummy-event')
        self.Song_position_auto()

    def asmr_stop(self):
        self.asmr_track_length = 0
        self.asmr_label.config(text='No track')
        self.song_position_scale.set(0)
        self.song_position_scale.config(state=tk.DISABLED)
        self.new_scale_position = 0

    def asmr_clear(self):
        if len(self.asmr_path) != 0:
            pygame.mixer.music.stop()
            self.asmr_stop()
            self.asmr_path.pop(self.asmr_pointer)
            self.asmr_pointer -= 1 #shift pointer backwards 
            self.asmr_load() #load the next song in list, if existing 

    def asmr_copy(self):
        #check that library/asmr directory exists
        if os.path.isdir("library/asmr") != True:
            self.post("./library/asmr/ directory does not exist, copying aborted.")
        else:   #check for duplicity of file
            file = os.path.join("library","asmr",Path(self.asmr_path[self.asmr_pointer]).name)
            if os.path.isfile(file) == False:
                self.post("Copying ASMR file into library directory...")
                shutil.copy2(self.asmr_path, file)
                self.post("Copying completed.")
            elif os.path.isfile(file) == True:
                self.post("A duplicate file exists in the same directory, copying aborted.")
                #TODO ask user if rename + copy is desired 


    def bgm_select(self, *others):
        if len(others) == 0:
            ans = tk.filedialog.askopenfilenames()
        else:
            ans = (others[0],)
        if len(ans) != 0:
            if len(self.bgm_path) !=0: #stop bgm track if already playing 
                self.bgm_path[self.bgm_pointer][0].stop()
            for file in ans:
                if self.assert_audio_file(file):
                    self.bgm_path.append((pygame.mixer.Sound(file),file,)) #tuple containing sound object and full path 
                    if self.copyv.get() == True:
                        self.bgm_pointer = len(self.bgm_path) - 1 
                        self.bgm_copy()
        else:
            return #abort if no file is selected
        self.bgm_pointer = len(self.bgm_path) - 1 

        self.bgm_load()

    def bgm_load(self):
        self.bgm_path[self.bgm_pointer][0].play(-1)
        self.bgm_label.config(text=Path(self.bgm_path[self.bgm_pointer][1]).stem)
        self.bgm_volume('dummy-event')
        self.post('BGM track loaded.')

    def bgm_stop(self):
        self.bgm_path[self.bgm_pointer][0].stop()
        self.bgm_label.config(text='No track')

    def bgm_clear(self):
        if len(self.bgm_path)!=0:

            self.bgm_stop()
            self.bgm_path.pop(self.bgm_pointer)
            self.bgm_pointer -= 1 

            self.bgm_load()
    
    def bgm_copy(self):
        #check that library/asmr directory exists
        if os.path.isdir("library/bgm") != True:
            self.post("./library/bgm/ directory does not exist, copying aborted.")
        else:   #check for duplicity of file
            file = os.path.join("library","bgm",Path(self.bgm_path[self.bgm_pointer][1]).name)
            print(file)
            if os.path.isfile(file) == False:
                self.post("Copying BGM file into library directory...")
                shutil.copy2(self.bgm_path[self.bgm_pointer][1], file) 
                self.post("Copying completed.")
            elif os.path.isfile(file) == True:
                self.post("A duplicate file already exists in the same directory, copying aborted.")
                #TODO ask user if rename + copy is desired 

    
    def Song_position_auto(*args): #stopped music starts when position is moved 
        self = args[0]
        if self.fasp == True:
            self.window.after(500, self.Song_position_auto)
        elif self.fasp == False: 
            if pygame.mixer.music.get_busy():
                self.song_position_scale.set(round(pygame.mixer.music.get_pos()/1000 /self.asmr_track_length,4) + self.new_scale_position)
                self.window.after(500, self.Song_position_auto)
            elif not pygame.mixer.music.get_busy(): #either asmr isn't loaded or manual song position was set
                if len(self.asmr_path) == 0:
                    pass
                else:
                    self.song_position_scale.set(0)
                    pygame.mixer.music.play(start = int(self.song_position_scale.get() * self.asmr_track_length))
                    self.new_scale_position = 0 
                    self.window.after(500, self.Song_position_auto)
        self.duration_str.set(f'{self.hhmmss(int(self.song_position_scale.get() * self.asmr_track_length))} / {self.hhmmss(self.asmr_track_length)}')

    def Song_position_manual(self,event):
        self.new_scale_position = self.song_position_scale.get()
        #pygame.mixer.music.stop() 
        pygame.mixer.music.play(start = int(self.song_position_scale.get() * self.asmr_track_length))
        self.fasp = False #re-enable auto-songposition after mouse button release event is detected
        self.duration_str.set(f'{self.hhmmss(int(self.song_position_scale.get() * self.asmr_track_length))} / {self.hhmmss(self.asmr_track_length)}')

    def Freeze_auto_song_position(self,event):
        self.fasp = True

    def muted(self,var,indx,mode):
        self.both_volume()

    def manual_function(self,var,indx,mode):
        if self.manualv.get() == True:
            self.automatic_directory_change.config(state=tk.DISABLED)
            self.automatic_directory_label.config(fg='grey')
        elif self.manualv.get() == False:
            self.automatic_directory_change.config(state=tk.NORMAL)
            self.automatic_directory_label.config(fg='black')
            

    def post(self,msg):
        self.messages.post(f'{time.strftime("%H:%M:%S", time.localtime())}: {msg}')
        self.log.config(text=self.messages.get())

    def hhmmss(self,seconds):
        return time.strftime('%H:%M:%S', time.gmtime(seconds))

    def foo(self):
        ans = tk.messagebox.askquestion('Confirmation Window','Are you sure you wish to proceed?')

    def asmr_left(self):
        if self.asmr_pointer > 0:
            self.asmr_stop()
            self.asmr_pointer -= 1
            self.asmr_load()
        elif self.asmr_pointer == 0 and len(self.asmr_path) > 1: #make list circular
            self.asmr_stop()
            self.asmr_pointer = len(self.asmr_path) - 1
            self.asmr_load()

    def asmr_right(self):
        if self.asmr_pointer < len(self.asmr_path) - 1:
            self.asmr_stop()
            self.asmr_pointer += 1
            self.asmr_load()
        elif self.asmr_pointer == len(self.asmr_path) - 1 and len(self.asmr_path) > 1:
            self.asmr_stop()
            self.asmr_pointer = 0 
            self.asmr_load() 

    def bgm_left(self):
        if self.bgm_pointer > 0:
            self.bgm_stop()
            self.bgm_pointer -= 1
            self.bgm_load()
        elif self.bgm_pointer == 0 and len(self.bgm_path) > 1: #make list circular
            self.bgm_stop()
            self.bgm_pointer = len(self.bgm_path) - 1
            self.bgm_load()


    def bgm_right(self):
        if self.bgm_pointer < len(self.bgm_path) - 1:
            self.bgm_stop()
            self.bgm_pointer += 1
            self.bgm_load() 
        elif self.bgm_pointer == len(self.bgm_path) - 1 and len(self.bgm_path) > 1:
            self.bgm_stop()
            self.bgm_pointer = 0 
            self.bgm_load() 
    

    def concatenate(self):
        pass 

    def exit(self):
        self.window.quit()
        # if tk.messagebox.askyesno(title='Confirmation', message="Are you sure you want to quit?"):
        #     self.window.quit()
        # else:
        #     pass
    
    def mute_hotkey(self, *others): #
        if self.mute_allv.get():
            self.mute_allv.set(False)
        elif not self.mute_allv.get():
            self.mute_allv.set(True)

    def help(self, *others):
        pass 

    def asmr_clear_all(self, *others):
        while len(self.asmr_path) != 0:
            self.asmr_clear()

    
    def bgm_clear_all(self, *others):
        while len(self.bgm_path) != 0:
            self.bgm_clear()