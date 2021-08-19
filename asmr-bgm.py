#Psuedo-code:
#1) Parse arguments from command line 
#2) Determine weights of each audio track if audio weights aren't specified 
#3) Use ffmpeg to mix 

import argparse

parser = argparse.ArgumentParser(description='Mixes a mimikaki audio trick with a bgm audio track.')
parser.add_argument('-a','--asmr',type=str,help='path to the ASMR audio file.', required=True)
parser.add_argument('-b', '--bgm', type=str,help='path to the BGM audio file', required=True)
parser.add_argument('-w', '--weight', type=str, help='weights of ASMR and BGM files, separated by a colon (e.g. 20:3)', default = 'auto')
args = parser.parse_args()

def asmr_bgm(asmr:str, bgm:str)->str:
    return asmr + bgm

if __name__ == '__main__':
    asmr_bgm(args.asmr, args.bgm)