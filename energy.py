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

# either 'All-Star' or 'Gloomy-Sunday' as of 4-11-2018
SONG_NAME = 'All-Star'
# SONG_NAME = 'Gloomy-Sunday'
SONG_PATH = os.path.join(os.getcwd(), 'test_songs', '{}.mp3'.format(SONG_NAME))
OUTPUT_SONG_PATH = os.path.join(os.getcwd(), 'test_songs', '{}-norm.mp3'.format(SONG_NAME))
try:
    os.remove(OUTPUT_SONG_PATH)
except OSError:
    pass

def json_from_stderr(stderr):
    json_result = '{' + stderr[1][:-2]
    json_result = json.loads(json_result)
    return json_result


def normalize(input_song_path, output_song_path, dual_pass=False):
    '''
    EBU R128 Definitions in (almost) plain english
    I: integrated loudness.  measured in LUFS. Spotify normalizes to -14 LUFS
    TP: True peak. Maximum permitted for a program is EBU R128 standard is -1.0 https://tech.ebu.ch/docs/r/r128.pdf
    LRA: loudness range. Difference between loud and soft parts of audio. Measured in LU. Between 6-12 is average, with 3 being heavily compressed, looped dance music, and 12 being dynamic indie rock.  (-95%FS to -10%FS Momentary, snapshot over sliding 3s window. Highest-Lowest)
    DR: dynamic range. DIFFERENT from LRA. Dynamic range is diff between highest peak and lowest trough

    loudnorm = subprocess.Popen(['ffmpeg', '-i', input_song_path, '-af',
                                'loudnorm=I=-14:TP=-1.0:LRA=20:print_format=json',
                                '-ar', '48k', output_song_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = loudnorm.communicate()

    json_loudnorm_results = json_from_stderr(stderr)
    print('loudness stats of {}: {}'.format(input_song_path, json_loudnorm_results))

    '''
    # TODO: use ffprobe to show stream information, then normalize with resulting settings like stereo, mono, sr, etc

    # Normalize audio. Do either a dual pass or a single pass.
    # For more info on dual-pass and single pass, refer to the creator of loudnorm: http://k.ylo.ph/2016/04/04/loudnorm.html

    if dual_pass == True:
        # Dual pass normalization: Do a dry run to get loudness related stats, then do a real run using stats from 1st pass to do more intelligent normalizatio
        loudnorm_dry_run = subprocess.Popen(['ffmpeg', '-i', input_song_path, '-af',
                                             'loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json',
                                             '-f', 'null', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = loudnorm_dry_run.communicate()
        stderr = stderr.decode('utf-8').split('{')
        json_loudnorm_results = json_from_stderr(stderr)
        print(json_loudnorm_results)
        measured_I = float(json_loudnorm_results['input_i'])
        measured_TP = float(json_loudnorm_results['input_tp'])
        measured_LRA = float(json_loudnorm_results['input_lra'])
        measured_thresh = float(json_loudnorm_results['input_thresh'])
        offset = float(json_loudnorm_results['target_offset'])
    
        # 2nd, pass those stats into loudnorm and tell it to save the output file
        loudnorm = subprocess.Popen(['ffmpeg', '-i', input_song_path, '-af', 'loudnorm=I=-14:TP=-1.0:LRA=20:measured_I={0}:measured_LRA={1}:measured_TP={2}:measured_thresh={3}:offset={4}:linear=true:print_format=json'.format(measured_I, measured_LRA, measured_TP, measured_thresh, offset),
                                 '-ar', '48k', output_song_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = loudnorm.communicate()
        stderr = stderr.decode('utf-8').split('{')
        json_loudnorm_results = json_from_stderr(stderr)
        loudness = float(json_loudnorm_results['output_i'])

    else:
        # Single pass normalization: Not as 'intelligent' as dual-pass (whatever THAT means), but twice as fast
        print('single pass norm')
        loudnorm = subprocess.Popen(['ffmpeg', '-i', input_song_path, '-af',
                                     'loudnorm=I=-14:TP=-1.0:LRA=20:print_format=json',
                                     '-ar', '48k', output_song_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = loudnorm.communicate()
        stderr = stderr.decode('utf-8').split('{')
        json_loudnorm_results = json_from_stderr(stderr)
        print('loudness stats of {}: {}'.format(input_song_path, json_loudnorm_results))
        loudness = float(json_loudnorm_results['output_i'])
    

    # Load normalized audio
    # TODO try even smaller durations when i get more songs later
    offset = 5.0
    duration = 15.0
    normalized_audio, sr = librosa.load(output_song_path, sr=22050, offset=offset, duration=duration) # read from file, O(1)
    return normalized_audio, loudness


def get_avg_beat_distance(normalized_audio):
    ndarr = np.ndarray(shape=(len(normalized_audio),), dtype=np.float32, buffer=normalized_audio) # cast to ndarr to pass to beat_track()
    tempo, beats = librosa.beat.beat_track(y=ndarr, sr=22050) # Original paper http://www.ee.columbia.edu/~dpwe/pubs/Ellis07-beattrack.pdf
    beat_times = librosa.frames_to_time(beats)
    print('tempo: ', tempo)
    print('beat times: ', beat_times)

    # calculate segment durations from beat times
    if len(beat_times) % 2 != 0:
        beat_times = beat_times[:-1]
    beat_distances = []
    for i in range(len(beat_times)-1):
        beat_distances.append(beat_times[i+1] - beat_times[i])

    avg_segment_duration = np.mean(beat_distances)
    return avg_segment_duration


def calculate_energy(avg_beat_distance, loudness):
    # combine segment durations and loudness
    # map between 0 and 1
    # Y = (X - A) / (B - A) * (D - C) + C
    print('avg segment duration: ', avg_beat_distance)
    print('loudness', loudness)
    energy = avg_beat_distance * loudness
    return energy

if __name__ == '__main__':
    # Time complexity of various python operations https://wiki.python.org/moin/TimeComplexity
    # Source code for loudnorm (to calculate time complexity: https://github.com/FFmpeg/FFmpeg/blob/7c82e0f61e365296b094684fd92aea0fe05ceb93/libavfilter/af_loudnorm.c
    # Beat_track algo paper: http://www.ee.columbia.edu/~dpwe/pubs/Ellis07-beattrack.pdf
    print(SONG_PATH)
    X, loudness = normalize(SONG_PATH, OUTPUT_SONG_PATH)
    print('{} samples loaded'.format(len(X)))
    avg_beat_distance = get_avg_beat_distance(X)
    energy = calculate_energy(avg_beat_distance, loudness)
    print('Energy: ', energy)
