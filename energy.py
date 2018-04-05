'''
Author: Luis Gomez
This program finds the energy of a song based on loudness and segment durations <- description borrowed from The Echo Nest
Metric inspired by The Echo Nest http://runningwithdata.com/post/1321504427/danceability-and-energy

Source for comparison songs:
All Star - Smashmouth: https://www.youtube.com/watch?v=Je_8A5hurSY
    Features: https://beta.developer.spotify.com/console/get-audio-features-track/?id=06AKEBrKUckW0KREUWRnvT

@whoislewys
'''

import librosa
import os
import sys
import subprocess
import time


SONG_PATH = r'C:\Users\lewys\Music\Rwr - Copy.mp3'
SPOTIFY_CLIENT_ID = 'a1abcafb905746b6b82840a2ff036a00'
SPOTIFY_CLIENT_SECRET = 'f391ff8c8c0649618641b27f9c0f2e50'


def normalize():
    # Start a subprocess
    # https://stackoverflow.com/questions/450285/executing-command-line-programs-from-within-python
    # Then use ffmpeg-normalize wi06AKEBrKUckW0KREUWRnvTthin that subprocess:
    # https://superuser.com/questions/323119/how-can-i-normalize-audio-using-ffmpeg/323127
    # ffmpeg-normalize "C:\Users\lewys\Music\Rwr - Copy.mp3" -of C:\Users\lewys\Music\RwrNORM -ext wav
    # THIS WORKS subprocess.check_output(['ffmpeg-normalize', SONG_PATH, '-of', r'C:\Users\lewys\Music\RwrNORM', '-ext', 'wav'])
    # get normalized_audio loudness here
    normalized_audio = librosa.load(os.path.join(os.getcwd, 'test_songs\\All Star.mp3')) # load audio samples, O(1)
    return normalized_audio


def getEnergy(normalized_audio):
    print(normalized_audio)



if '__name__' == '__main__':
    X = normalize()
    getEnergy(X)
