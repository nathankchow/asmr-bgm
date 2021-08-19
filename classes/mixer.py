#handles the mixing and concatenating of audio files using ffmpeg 
import os
from pathlib import Path
import subprocess
import librosa
from math import ceil
import logging

class Mixer:
    def __init__(self):
        pass

    def mix(self, asmr_file, bgm_file, weights): #weights should be tuple (asmr_file_weight, bgm_file_weight)
        logging.info(f'asmr_file: {asmr_file}\nbgm_file: {bgm_file}\nweights:{weights}\n')
        def audio_length(file):
            return librosa.get_duration(filename=file)
        
        output_filename = 'temp.mp3' #TODO: make filename dependent asmr file, bgm file, weights, and date/time
        asmr_length = audio_length(asmr_file)
        bgm_length = audio_length(bgm_file)
        if asmr_length > bgm_length: #loop bgm
            loop_number = ceil(asmr_length/bgm_length)
            bgm_file = Mixer.concatenate_pt1(bgm_file, loop_number)
        asmr_weight, bgm_weight = weights #unpack tuple
        subprocess.run(f'ffmpeg -i "{asmr_file}" -i "{bgm_file}" -filter_complex amix=inputs=2:duration=first:dropout_transition=2:weights="{asmr_weight} {bgm_weight}" "{Path(asmr_file).stem}_{Path(bgm_file).stem}_{int(1000*asmr_weight)}_{int(1000*bgm_weight)}.mp3"')
        if asmr_length > bgm_length:
            os.remove(bgm_file)


    def concatenate_pt1(files,number=1):
        if os.path.exists('temp/temp.txt'):
            os.remove('temp/temp.txt')
        if type(files) == str:
            split_filename = files.rsplit('.',1)
            subprocess.run(f'ffmpeg -stream_loop {number} -i "{files}" -c copy "{split_filename[0]}_loop_{number}.{split_filename[1]}"')
            return f'{split_filename[0]}_loop_{number}.{split_filename[1]}'
        else:
            f= open('temp/temp.txt',mode="w+",encoding='utf-8')
            file_list = [f"file '{file}'" for file in files]
            f.write('\n'.join(file_list))
            print('done')
            
    def concatenate_pt2(new_file_name): #two-part process because subprocess needs pt1 to resolve before working (for unknown reason)
        print('concat.pt2')
        
        subprocess.run(f'ffmpeg -f concat -safe 0 -i temp/temp.txt -c copy "{new_file_name}"')
        os.remove('temp/temp.txt')

    def convert_to_mp3(files):
        for file in files:
            name = Path(file).stem
            subprocess.run(f'ffmpeg -i "{file}" "{name}.mp3"')


if __name__ == "__main__":
    mixer = Mixer()
