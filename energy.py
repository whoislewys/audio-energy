'''
Author: Luis Gomez
This program finds the energy of a song based on loudness and segment durations <- description borrowed from The Echo Nest
Metric inspired by The Echo Nest http://runningwithdata.com/post/1321504427/danceability-and-energy
@whoislewys
'''
import librosa
import subprocess

SONG_PATH = r'C:\Users\lewys\Music\Rwr - Copy.mp3'


def normalize():
    # Start a subprocess
    # https://stackoverflow.com/questions/450285/executing-command-line-programs-from-within-python
    # Then use ffmpeg-normalize within that subprocess:
    # https://superuser.com/questions/323119/how-can-i-normalize-audio-using-ffmpeg/323127
    # ffmpeg-normalize "C:\Users\lewys\Music\Rwr - Copy.mp3" -of C:\Users\lewys\Music\RwrNORM -ext wav
    subprocess.check_output(['ffmpeg-normalize', SONG_PATH, '-of', r'C:\Users\lewys\Music\RwrNORM', '-ext', 'wav'])


if '__name__' == '__main__':
    normalize()