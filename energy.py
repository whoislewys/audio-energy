"""
Author: Luis Gomez
This program finds the energy of a song based on loudness and segment durations <- description borrowed from The Echo Nest
Metric inspired by The Echo Nest http://runningwithdata.com/post/1321504427/danceability-and-energy

Source for comparison songs:
Raining Blood - Slayer
    Youtube: https://www.youtube.com/watch?v=6M4HtTZ8iGM
    Spotify: https://open.spotify.com/track/01Mpj13vURSO3cCLprPt5T

All Star - Smashmouth
    Youtube: https://www.youtube.com/watch?v=Je_8A5hurSY
    Spotify: https://open.spotify.com/track/3cfOd4CMv2snFaKAnMdnvK

Gloomy Sunday (Take 1) - Billie Holiday
    Youtube: https://www.youtube.com/watch?v=MNHz_rS6Kk0
    Spotify: https://open.spotify.com/track/41CHb7F7SXcmkj0h8wekeF

Suede - NxWorries
    Youtube: https://www.youtube.com/watch?v=OpVxEvCu0xE
    Spotify: https://open.spotify.com/tracks/4F07ku5lMBIoybFPStM2j4

Im Your Hoochie Coochie Man - Muddy Waters
    Youtube: https://www.youtube.com/watch?v=2F7w4zLq4G0
    Spotify: https://open.spotify.com/track/3KSchPNSklO5McIqRH3qYX

Im Glad - Captain Beefhesat
    Youtube: https://www.youtube.com/watch?v=M59puEnSvd8
    Spotify: https://open.spotify.com/track/6vcF9napv3kwm8rSb4O2si

I Will Always Love You - Whitney Houston
    Youtube: https://www.youtube.com/watch?v=tP0zj220CbQ
    Spotify: https://open.spotify.com/track/4eHbdreAnSOrDDsFfc4Fpm

Stolen Moments - Oscar Peterson
    Youtube: https://www.youtube.com/watch?v=MWTTFSgulGA
    Spotify: https://open.spotify.com/album/7BSQKjtu7YjBkTuhBK2tIJ

YOUTUBE SONGS ARE ONLY FOR EDUCATIONAL USE, NOT REDISTRIBUTION
To download the Youtube links, install youtube-dl and use the command
youtube-dl -x --audio-quality 0 --audio-format mp3 <link>
-x to extract, --audio-quality 0 for best possible quality, --audio-format mp3 for .mp3 file

Author: @whoislewys
E-mail: lagomez8@asu.edu
Alt e-mail: whoislewys@gmail.com
"""

import librosa
import numpy as np
import os
import subprocess
import json

# either 'All-Star' or 'Gloomy-Sunday' as of 4-11-2018
#SONG_NAMES = {'Raining-Blood', 'All-Star', 'Suede', 'Hooch-Cooch', 'Im-Glad', 'I-Will-Always-Love-You', 'Stolen-Moments', 'Gloomy-Sunday'}
SONG_NAMES = {'Raining-Blood', 'All-Star', 'Hooch-Cooch', 'I-Will-Always-Love-You', 'Stolen-Moments', 'Gloomy-Sunday'}
SONG_PATHS = [os.path.join(os.getcwd(), 'test_songs', '{}.mp3'.format(song_name)) for song_name in SONG_NAMES]
NORM_SONG_PATHS = [os.path.join(os.getcwd(), 'test_songs', '{}-13LUFS-norm.mp3'.format(song_name)) for song_name in SONG_NAMES]

OFFSET = 10.0
DURATION = 15.0

def json_from_stderr(stderr):
    json_result = '{' + stderr[1][:-2]
    json_result = json.loads(json_result)
    return json_result


def normalize(input_song_path, output_song_path):
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

    # get loudness stats
    loudnorm_dry_run = subprocess.Popen(['ffmpeg', '-i', input_song_path, '-af', 'loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json',
                                         '-f', 'null','-'],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = loudnorm_dry_run.communicate()
    stderr = stderr.decode('utf-8').split('{')
    json_result = '{' + stderr[1][:-2]
    loudnorm_results_json = json.loads(json_result)
    measured_I = float(loudnorm_results_json['input_i'])
    loudness = measured_I

    # Load newly normalized audio
    # print('loudness stats of {}: {}'.format(input_song_path, json_loudnorm_results))
    # TODO try even smaller durations when i get more songs later
    offset = OFFSET
    duration = DURATION
    normalized_audio, sr = librosa.load(output_song_path, sr=22050, offset=offset, duration=duration) # read from file, O(1)
    return normalized_audio, loudness


def get_avg_beat_distance(normalized_audio):
    ndarr = np.ndarray(shape=(len(normalized_audio),), dtype=np.float32, buffer=normalized_audio) # cast to ndarr to pass to beat_track()
    tempo, beats = librosa.beat.beat_track(y=ndarr, sr=22050, hop_length=512, tightness=100.0, units='time') # Original paper http://www.ee.columbia.edu/~dpwe/pubs/Ellis07-beattrack.pdf
    #beat_times = librosa.frames_to_time(beats)

    #calculate segment durations from beat times
    beat_times = beats
    if len(beat_times) % 2 != 0:
        beat_times = beat_times[:-1]
    beat_distances = []
    for i in range(len(beat_times)-1):
        beat_distances.append(beat_times[i+1] - beat_times[i])

    avg_segment_duration = np.mean(beat_distances)
    return avg_segment_duration

    # # try using librosa segments instead of beats
    # chroma = librosa.feature.chroma_cqt(normalized_audio, hop_length=256)
    # bounds = librosa.segment.agglomerative(chroma, k=20)
    # #print(bounds)
    # bound_times = librosa.frames_to_time(bounds)
    #
    # # get avg segment dur
    # segment_durations = []
    # for i in range(len(bound_times) - 1):
    #     segment_durations.append(bound_times[i+1] - bound_times[i])
    #
    # avg_segment_duration = np.mean(segment_durations)
    # return avg_segment_duration


def calculate_energy(avg_beat_distance, loudness):
    # combine segment durations and loudness
    # map between 0 and 1
    # Y = (X - A) / (B - A) * (D - C) + C
    print('raw loudness', loudness)
    print('raw beat distance: ', avg_beat_distance)
    scaled_loudness = loudness * -1
    scaled_avg_beat_distance = np.power(avg_beat_distance,2)
    print('scld loudness: ', scaled_loudness)
    print('scld beat distance: ', scaled_avg_beat_distance)

    energy = scaled_loudness + avg_beat_distance
    energy = 1/np.power((1.4*energy), 1.95)
    energy = energy * 100
    return energy


if __name__ == '__main__':
    print(SONG_PATHS[2])
    print(NORM_SONG_PATHS[2])
    exit()
    normalized_samples, loudness = normalize(SONG_PATHS[0], NORM_SONG_PATHS[0])
    avg_beat_distance = get_avg_beat_distance(normalized_samples)
    energy = calculate_energy(avg_beat_distance, loudness)
    print('Energy: ', energy)
	
    # for song_name in SONG_NAMES:
    #     print(song_name)
    #     input_path = os.path.join(os.getcwd(), 'test_songs', '{}.mp3'.format(song_name))
    #     output_path = os.path.join(os.getcwd(), 'test_songs', '{}-13LUFS-norm.mp3'.format(song_name))
    #     if os.path.exists(output_path):
    #         print('song exists, skipping')
    #     else:
    #         X, loudness = normalize(input_path, output_path)
    #         print('{} samples loaded'.format(len(X)))
    #         avg_beat_distance = get_avg_beat_distance(X)
    #         energy = calculate_energy(avg_beat_distance, loudness)

    # # get just segment duration from song name list
    # for song_name in SONG_NAMES:
    #     print()
    #     print(song_name.lower().replace('-', '_') + '_seg_dur')
    #     load_path = os.path.join(os.getcwd(), 'test_songs', '{}-13LUFS-norm.mp3'.format(song_name))
    #     offset = OFFSET
    #     duration = DURATION
    #     X, sr = librosa.load(load_path, sr=22050, offset=offset, duration=duration)
    #     avg_segment_dur = get_avg_beat_distance(X)
    #     print(avg_segment_dur)