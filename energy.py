'''
Author: Luis Gomez
This program finds the energy of a song based on loudness and segment durations <- description borrowed from The Echo Nest
Metric inspired by The Echo Nest http://runningwithdata.com/post/1321504427/danceability-and-energy

Source for comparison songs:
All Star - Smashmouth
    Youtube: https://www.youtube.com/watch?v=Je_8A5hurSY
    Spotify: https://open.spotify.com/track/3cfOd4CMv2snFaKAnMdnvK
    Features: https://beta.developer.spotify.com/console/get-audio-features-track/?id=06AKEBrKUckW0KREUWRnvT

Gloomy Sunday (Take 1) - Billie Holiday
    Youtube: https://www.youtube.com/watch?v=MNHz_rS6Kk0
    Spotify: https://open.spotify.com/track/41CHb7F7SXcmkj0h8wekeF
    Features:
@whoislewys
'''

import librosa
import numpy as np
import os
import sys
import subprocess
import json
import time

SONG_NAME = 'Gloomy-Sunday'
SONG_PATH = r'C:\Users\lewys\PycharmProjects\audio-energy\test_songs\{}.mp3'.format(SONG_NAME)
OUTPUT_SONG_PATH = r'C:\Users\lewys\PycharmProjects\audio-energy\test_songs\{}-norm.mp3'.format(SONG_NAME)


def normalize(song_path):
    # TODO try even smaller durations when i get more songs later
    # Time complexity of various python operations https://wiki.python.org/moin/TimeComplexity
    # Source code for loudnorm (to calculate time complexity: https://github.com/FFmpeg/FFmpeg/blob/7c82e0f61e365296b094684fd92aea0fe05ceb93/libavfilter/af_loudnorm.c
    # ffmpeg -i Rwr.mp3 -filter:a loudnorm Rwr-norm.mp3
    # -af set audio filters
    # ffmpeg -i in.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null -
    # ffmpeg -i in.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=-27.61:measured_LRA=18.06:measured_TP=-4.47:measured_thresh=-39.20:offset=0.58:linear=true:print_format=summary -ar 48k out.wav
    # TODO: try to get ffmpeg output from normalize
    print(song_path)
    # I: integrated loudness.  measured in LUFS. Spotify normalizes to -14 LUFS
    # TP: True peak. Maximum permitted for a program is EBU R128 standard is -1.0 https://tech.ebu.ch/docs/r/r128.pdf
    # LRA: loudness range. Difference between loud and soft parts of audio. Measured in LU. Between 6-12 is average, with 3 being heavily compressed, looped dance music, and 12 being dynamic indie rock.  (-95%FS to -10%FS Momentary, snapshot over sliding 3s window. Highest-Lowest)
    # DR: dynamic range. DIFFERENT from LRA. Dynamic range is diff between highest peak and lowest trough
    # "-i", filepath, "-filter_complex", "ebur128", "-f", "null", "-")
    ffmpeg_ebur128 = subprocess.Popen(['ffmpeg', '-i', song_path, '-filter_complex', 'ebur128', '-f', 'null', '-'], stderr=subprocess.PIPE)
    #ffmpeg_normalize = subprocess.Popen(['ffmpeg', '-i', song_path, '-af', 'loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json', '-f', 'null', '-'],
    # stdout=subprocess.PIPE, stderr=subprocess.PIPE);
    # get the json from ffmpeg output

    stdout, stderr = ffmpeg_ebur128.communicate()
    print('stdout: ', stdout)
    print('stderr: ', stderr)
    json_output = json.loads(output)
    print(json_output)
    print('end of output')
    print()

    subprocess.check_output(['ffmpeg', '-i', song_path, '-filter:a', 'loudnorm', OUTPUT_SONG_PATH])
    offset = 5.0
    duration = 15.0
    normalized_audio, sr = librosa.load(song_path, sr=22050, offset=offset, duration=duration) # read from file, O(1)
    return normalized_audio, loudness


def getEnergy(normalized_audio):
    '''
    loudness and segment durations
    '''
    energy = 0.0
    ndarr = np.ndarray(shape=(len(normalized_audio),), dtype=np.float32, buffer=normalized_audio)

    tempo, beats = librosa.beat.beat_track(y=ndarr, sr=22050) # http://www.ee.columbia.edu/~dpwe/pubs/Ellis07-beattrack.pdf
    beat_times = librosa.frames_to_time(beats)
    print('tempo: ', tempo)
    print('beat times: ', beat_times)

    # calculate segment durations from beat times
    if len(beat_times) % 2 != 0:
        beat_times = beat_times[:-1]

    # get beat distances with list comprehension
    beat_distances_1 = [(beat_times[n] - beat_times[n-1]) for counter, n in enumerate(beat_times, start=1)]
    beat_distances = []
    for i in range(len(beat_times)-1):
        beat_distances.append(beat_times[i+1] - beat_times[i])

    print(beat_distances_1)
    print(beat_distances)

    avg_segment_duration = np.mean(beat_distances)
    print('avg segment duration: ', avg_segment_duration)

    '''
    # get loudness stats
    # ffmpeg -i in.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null -
    We can then use these stats to call FFmpeg for a second time.
    Supplying the filter with these stats allow it to make more intelligent normalization decisions, as well as normalize linearly if possible.
    This second pass creates the loudness normalized output file, and prints a human-readable stats summary to stderr.
    # ffmpeg -i in.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=-27.61:measured_LRA=18.06:measured_TP=-4.47:measured_thresh=-39.20:offset=0.58:linear=true:print_format=summary -ar 48k out.wav
    # SOURCE: http://k.ylo.ph/2016/04/04/loudnorm.html
    '''

    # combine segment durations and loudness

    # map between 0 and 1
    # Y = (X - A) / (B - A) * (D - C) + C

    return energy


if __name__ == '__main__':
    X = normalize(SONG_PATH)
    print('{} samples loaded'.format(len(X)))
    getEnergy(X)
