"""
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
"""

import librosa
import numpy as np
import os
import sys
import subprocess
import json
import time

# either 'All-Star' or 'Gloomy-Sunday' as of 4-11-2018
# SONG_NAME = 'All-Star'
SONG_NAME = 'Gloomy-Sunday'
SONG_PATH = os.path.join(os.getcwd(), 'test_songs', '{}.mp3'.format(SONG_NAME))
OUTPUT_SONG_PATH = os.path.join(os.getcwd(), 'test_songs', '{}-13LUFS-norm.mp3'.format(SONG_NAME))
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
    Normalize audio. Do either a dual pass or a single pass. (single by default.)
    For more info on dual-pass and single pass, refer to the creator of loudnorm: http://k.ylo.ph/2016/04/04/loudnorm.html

    EBU R128 DEFINITIONS IN (ALMOST) PLAIN ENGLISH
    I: integrated loudness.  measured in LUFS. Spotify normalizes to -14 LUFS
    TP: True peak. Maximum permitted for a program is EBU R128 standard is -1.0 https://tech.ebu.ch/docs/r/r128.pdf
    LRA: loudness range. Difference between loud and soft parts of audio. Measured in LU. Between 6-12 is average, with 3 being heavily compressed, looped dance music, and 12 being dynamic indie rock.  (-95%FS to -10%FS Momentary, snapshot over sliding 3s window. Highest-Lowest)
    DR: dynamic range. DIFFERENT from LRA. Dynamic range is diff between highest peak and lowest trough
    '''
    output_file_name = input_song_path.split('.mp3')[0] + '-13LUFSnorm.mp3'
    # Get stream information using ffprobe, then normalize with appropriate samplerate, stereo/mono settings
    ffprobe_results = subprocess.check_output(['ffprobe', '-show_streams', '-of', 'json', '-loglevel', '0', input_song_path])
    json_stream_info = json.loads(ffprobe_results.decode('utf-8'))
    input_sr = json_stream_info['streams'][0]['sample_rate']
    # Get Integrated Loudness in LUFS by doing a loudnorm dry run
    loudnorm_dry_run = subprocess.Popen(['ffmpeg', '-i', input_song_path, '-af', 'loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json',
                                         '-f', 'null', '-'],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = loudnorm_dry_run.communicate()
    stderr = stderr.decode('utf-8').split('{')
    json_result = '{' + stderr[1][:-2]
    loudnorm_results_json = json.loads(json_result)
    measured_I = float(loudnorm_results_json['input_i'])
    # Normalize audio to -14 LUFS using RMS volume
    target_volume = -13
    gain = target_volume - measured_I
    # print('applying {}dB of gain'.format(gain))
    subprocess.call(['ffmpeg', '-i', input_song_path, '-af', 'volume={}dB'.format(gain), '-ar', input_sr, output_song_path])
    loudnorm_dry_run = subprocess.Popen(['ffmpeg', '-i', input_song_path, '-af', 'loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json',
                                         '-f', 'null','-'],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = loudnorm_dry_run.communicate()
    stderr = stderr.decode('utf-8').split('{')
    json_result = '{' + stderr[1][:-2]
    loudnorm_results_json = json.loads(json_result)
    measured_I = float(loudnorm_results_json['input_i'])
    loudness = measured_I

    # print('loudness stats of {}: {}'.format(input_song_path, json_loudnorm_results))
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
    print('raw loudness', loudness)
    print('raw beat distance: ', avg_beat_distance)
    scaled_loudness = np.power(loudness * -1 - 4, 4)
    scaled_avg_beat_distance = np.power(avg_beat_distance * 2, 8) * 100
    print('scld loudness: ', scaled_loudness)
    print('scld beat distance: ', scaled_avg_beat_distance)
    raw_energy = scaled_avg_beat_distance + scaled_loudness
    print('raw energy: ', raw_energy)
    energy = raw_energy/20000
    print('Energy: ', energy)
    return energy


if __name__ == '__main__':
    # Time complexity of various python operations https://wiki.python.org/moin/TimeComplexity
    # Source code for loudnorm (to calculate time complexity: https://github.com/FFmpeg/FFmpeg/blob/7c82e0f61e365296b094684fd92aea0fe05ceb93/libavfilter/af_loudnorm.c
    # Beat_track algo paper: http://www.ee.columbia.edu/~dpwe/pubs/Ellis07-beattrack.pdf
    # print(SONG_PATH)
    # X, loudness = normalize(SONG_PATH, OUTPUT_SONG_PATH)
    # print('{} samples loaded'.format(len(X)))
    # avg_beat_distance = get_avg_beat_distance(X)
    # energy = calculate_energy(avg_beat_distance, loudness)

    all_star_beat_dist = 0.5774701764763875
    all_star_loudness = -9.37
    gloomy_beat_dist = 0.879262282690854
    gloomy_loudness = -13.34

    print()
    print('All Star')
    all_star_energy = calculate_energy(all_star_beat_dist, all_star_loudness)

    print()
    print('Gloomy Sunday')
    gloomy_energy = calculate_energy(gloomy_beat_dist, gloomy_loudness)

