import os
import sys
from pathlib import Path
import subprocess
from math import ceil
import shutil
import time
import queue
import threading
import random

class Writer:
    def __init__(self):
        pass

    def emptyTempFolder(self):
        for file in os.listdir('temp'):
            os.remove(os.path.join('temp',file))

    def getDuration(self,filename):
        #uses ffprobe to get duration of audio file 
        PROBE_DST = 'temp/metadata.txt'
        if os.path.exists(PROBE_DST):
            os.remove(PROBE_DST)
        os.system(
            f'ffprobe -show_data -show_streams "{filename}" > {PROBE_DST}'
        )
        with open(PROBE_DST) as f:
            s = f.read() 
        
        #parse string for duration 
        l = s.split('\n')
        for s in l: 
            if 'duration=' in s:
                duration = s[len('duration='):]
                duration = float(duration)
                break
        
        #cleanup
        if os.path.exists(PROBE_DST):
            os.remove(PROBE_DST)
        
        return duration 

    def concatenate(self, files, dst = 'temp', name=False):
        #concatenates all audio files listed in an iterable, and returns the location of the concatenated file
        if os.path.exists('temp/temp.txt'):
            os.remove('temp/temp.txt')
        os.path.basename(Path('C:/users/natha/desktop/dearlybeloved3582.mp3').parent)

        with open('temp/temp.txt',mode="w+",encoding='utf-8') as f:
            file_list = [f"file '{file}'" for file in files]
            f.write('\n'.join(file_list))

        if name==False: 
            name = f'temp/{os.path.basename(Path(files[0]).parent)}.wav'

        subprocess.run(f'ffmpeg -f concat -safe 0 -i temp/temp.txt "{name}"')
        shutil.copy2(src='temp/temp.txt', dst = 'C:/users/natha/desktop/temp33.txt')
        os.remove('temp/temp.txt')

        return name

    
    def loop(self,bgm_file,loop_number):
        dst = 'temp/looped' + Path(bgm_file).suffix
        #loops an audio file a specified number of times, and outputs to temp folder
        subprocess.run(f'ffmpeg -stream_loop {loop_number} -y -i "{bgm_file}" -c copy "{dst}"')
        #return location of looped file
        return dst

    def mix(self,asmr_file,bgm_file,asmr_weight,bgm_weight,format, app = None, dst = 'library/output'):

        if format == "Same as ASMR":
            print("format 1", format)
            format = Path(asmr_file).suffix 
            print("format 2", format)
        elif format[0] != '.':
            format = '.' + format #make sure suffix has dot at beginning 

        #get lengths of both files
        asmr_length = self.getDuration(asmr_file)
        bgm_length = self.getDuration(bgm_file)

        #loop bgm file if shorter than asmr file 
        if asmr_length > bgm_length:
            loop_number = ceil(asmr_length/bgm_length)
            bgm_file_processed = self.loop(bgm_file, loop_number)
        else:
            bgm_file_processed = bgm_file
        dst = f"library/output/{Path(asmr_file).stem}_{Path(bgm_file).stem}_{int(asmr_weight)}_{int(bgm_weight)}{format}"
        dst = os.path.join(os.getcwd(),dst)
        cmd = f'ffmpeg -i "{asmr_file}" -i "{bgm_file_processed}" -filter_complex amix=inputs=2:duration=first:dropout_transition=2:weights="{asmr_weight} {bgm_weight}" "{dst}"'
        
        subprocess.run(f'ffmpeg -i "{asmr_file}" -i "{bgm_file_processed}" -filter_complex amix=inputs=2:duration=first:dropout_transition=2:weights="{asmr_weight} {bgm_weight}" "{dst}"')
        
        print(app)
        if app != None: 
            print('posting stomethign')
            app.post(f"Mixing of {dst} complete.")

    def convert_to_mp3(self,files):
        #takes an iterable containing file names and converts them to mp3s 
        for file in files:
            name = Path(file).stem
            subprocess.run(f'ffmpeg -i "{file}" "{name}.mp3"')
 
class WriterQueue(queue.Queue):
    def __init__(self):
        super().__init__()

class Consumer(threading.Thread):
    def __init__(self, wq):
        self.wq = wq #writer queue instance  
        super().__init__(daemon=True)
        self.busy = False
    
    def run(self):
        while True:
            if self.wq.empty() == False:    
                task = self.wq.get()
                self.busy = True
                task[0](*task[1]) #takes tuple of length 2 containing callable and arguments 
                self.busy = False
            time.sleep(1)


