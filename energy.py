"""
Author: Luis Gomez
This program finds the energy of a song based on loudness and segment durations <- description borrowed from The Echo Nest
Metric inspired by The Echo Nest http://runningwithdata.com/post/1321504427/danceability-and-energy

Source for comparison songs:
Raining Blood - Slayer
    Youtube: https://www.youtube.com/watch?v=6M4HtTZ8iGM
    Spotify: https://open.spotify.com/album/2DumvqHl78bNXuvU9kQfPN

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
import sys
import subprocess
import json
import time

# either 'All-Star' or 'Gloomy-Sunday' as of 4-11-2018
#SONG_NAMES = {'Raining-Blood', 'All-Star', 'Suede', 'Hooch-Cooch', 'Im-Glad', 'I-Will-Always-Love-You', 'Stolen-Moments', 'Gloomy-Sunday'}
SONG_NAMES = {'Raining-Blood', 'All-Star', 'Hooch-Cooch', 'I-Will-Always-Love-You', 'Stolen-Moments', 'Gloomy-Sunday'}
SONG_PATHS = set(os.path.join(os.getcwd(), 'test_songs', '{}.mp3'.format(song_name)) for song_name in SONG_NAMES)
OUTPUT_SONG_PATHS = set(os.path.join(os.getcwd(), 'test_songs', '{}-13LUFS-norm.mp3'.format(song_name)) for song_name in SONG_NAMES)

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

    print('Energy: ', energy)
    return energy


if __name__ == '__main__':
    # Time complexity of various python operations https://wiki.python.org/moin/TimeComplexity
    # Source code for loudnorm (to calculate time complexity: https://github.com/FFmpeg/FFmpeg/blob/7c82e0f61e365296b094684fd92aea0fe05ceb93/libavfilter/af_loudnorm.c
    # Beat_track algo paper: http://www.ee.columbia.edu/~dpwe/pubs/Ellis07-beattrack.pdf

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

    
    # dur 15 off 10
    # raining_blood_seg_dur = 0.7381501372478816
    # all_star_seg_dur = 0.723484902733023
    # suede_seg_dur = 0.7723690177825516
    # hooch_cooch_seg_dur = 0.7503711660102638
    # im_glad_seg_dur = 0.7515932688865019
    # i_will_always_love_you_seg_dur = 0.7760353264112663
    # stolen_moments_seg_dur = 0.7613700918964077
    # gloomy_sunday_seg_dur = 0.7418164458765962
    #
    # # dur 30 off 10
    # raining_blood_seg_dur = 1.2428786251342643
    # all_star_seg_dur = 1.5215180809165771
    # suede_seg_dur = 1.5007423320205278
    # hooch_cooch_seg_dur = 1.4323045709511875
    # im_glad_seg_dur = 1.4261940565699964
    # i_will_always_love_you_seg_dur = 1.4225277479412817
    # stolen_moments_seg_dur = 1.5190738751641006
    # gloomy_sunday_seg_dur = 1.52640649242153

    r_blood_beat_dist = 0.3799628942486086
    r_blood_loudness = -7.26
    all_star_beat_dist = 0.5764606132307997
    all_star_loudness = -9.37
    suede_beat_dist = 0.45318945969192276
    suede_loudness = -9.18
    hooch_cooch_beat_dist = 0.8111504157218443
    hooch_cooch_loudness = -12.98
    im_glad_beat_dist = 0.39672951085195984
    im_glad_loudness = -10.29
    i_will_always_love_you_beat_dist = 0.7308175199904523
    i_will_always_love_you_loudness = -14.56
    stolen_moments_beat_dist = 0.5360780834072759
    stolen_moments_loudness = -14.1
    gloomy_beat_dist = 0.37214684071826926
    gloomy_loudness = -13.34

    # dur 30 off 10 beat dist
    # r_blood_beat_dist = 0.3762904979343336
    # all_star_beat_dist = 0.5764606132307997
    # hooch_cooch_beat_dist = 0.8216867822397775
    # i_will_always_love_you_beat_dist = 0.5149669942050894
    # stolen_moments_beat_dist = 0.5386118892001245
    # gloomy_beat_dist = 0.7096970754113611

    print('\nR blood')
    r_blood_energy = calculate_energy(r_blood_beat_dist, r_blood_loudness)
    print('\nAll Star')
    all_star_energy = calculate_energy(all_star_beat_dist, all_star_loudness)
    print('\nSuede')
    suede_energy = calculate_energy(suede_beat_dist, suede_loudness)
    print('\nHooch_Cooch')
    hooch_cooch_energy = calculate_energy(hooch_cooch_beat_dist, hooch_cooch_loudness)
    #print('\nIm Glad')
    #im_glad_energy = calculate_energy(im_glad_beat_dist, im_glad_loudness)
    print('\n I Will Always Love You')
    i_will_always_love_you_energy = calculate_energy(i_will_always_love_you_beat_dist, i_will_always_love_you_loudness)
    print('\n Stolen Moments')
    stolen_moments_energy = calculate_energy(stolen_moments_beat_dist, stolen_moments_loudness)
    print('\nGloomy Sunday')
    gloomy_energy = calculate_energy(gloomy_beat_dist, gloomy_loudness)


# Spotify avg segment durations
# all_star 0.0035613178294573644
# i will always love you 0.0044417647058823525
'''
segments = [
    {
      "start": 10.05478,
      "duration": 0.2951,
      "confidence": 0.334,
      "loudness_start": -13.797,
      "loudness_max_time": 0.10026,
      "loudness_max": -8.9,
      "pitches": [
        0.107,
        0.866,
        0.298,
        0.061,
        0.084,
        0.284,
        1,
        0.234,
        0.111,
        0.073,
        0.05,
        0.037
      ],
      "timbre": [
        47.287,
        28.932,
        12.908,
        -10.055,
        17.452,
        -15.692,
        -1.652,
        6.644,
        -17.271,
        14.226,
        -25.676,
        32.472
      ]
    },
    {
      "start": 10.34989,
      "duration": 0.27315,
      "confidence": 0.858,
      "loudness_start": -22.962,
      "loudness_max_time": 0.09764,
      "loudness_max": -11.461,
      "pitches": [
        0.15,
        0.09,
        0.052,
        0.043,
        0.064,
        0.082,
        0.051,
        0.04,
        0.058,
        0.132,
        1,
        0.393
      ],
      "timbre": [
        42.559,
        72.28,
        -25.643,
        -45.569,
        25.151,
        10.083,
        -12.685,
        -33.108,
        3.298,
        -6.597,
        -41.058,
        -2.339
      ]
    },
    {
      "start": 10.62304,
      "duration": 0.59896,
      "confidence": 1,
      "loudness_start": -24.286,
      "loudness_max_time": 0.07213,
      "loudness_max": -3.929,
      "pitches": [
        1,
        0.405,
        0.185,
        0.119,
        0.129,
        0.164,
        0.152,
        0.3,
        0.621,
        0.389,
        0.554,
        0.264
      ],
      "timbre": [
        46.406,
        147.889,
        62.403,
        -42.833,
        37.728,
        27.183,
        0.888,
        -25.901,
        -5.229,
        11.377,
        -51.732,
        25.311
      ]
    },
    {
      "start": 11.222,
      "duration": 0.31224,
      "confidence": 0.942,
      "loudness_start": -21.138,
      "loudness_max_time": 0.06114,
      "loudness_max": -8.308,
      "pitches": [
        0.146,
        1,
        0.11,
        0.226,
        0.106,
        0.059,
        0.069,
        0.046,
        0.391,
        0.105,
        0.067,
        0.057
      ],
      "timbre": [
        46.188,
        54.23,
        29.726,
        -44.496,
        22.199,
        27.358,
        25.664,
        -45.04,
        -15.772,
        24.803,
        -12.281,
        6.433
      ]
    },
    {
      "start": 11.53424,
      "duration": 0.24989,
      "confidence": 0.855,
      "loudness_start": -19.507,
      "loudness_max_time": 0.0436,
      "loudness_max": -5.803,
      "pitches": [
        0.075,
        0.375,
        0.057,
        0.095,
        0.129,
        0.25,
        1,
        0.112,
        0.163,
        0.049,
        0.11,
        0.036
      ],
      "timbre": [
        50.25,
        147.031,
        12.199,
        47.115,
        24.044,
        -2.454,
        -60.227,
        -5.997,
        0.461,
        -2.691,
        -36.848,
        14.416
      ]
    },
    {
      "start": 11.78413,
      "duration": 0.3307,
      "confidence": 0.992,
      "loudness_start": -20.381,
      "loudness_max_time": 0.0644,
      "loudness_max": -6.374,
      "pitches": [
        0.157,
        0.601,
        0.172,
        0.237,
        0.245,
        0.519,
        1,
        0.214,
        0.154,
        0.101,
        0.148,
        0.114
      ],
      "timbre": [
        46.856,
        129.222,
        50.428,
        -32.929,
        20.544,
        43.109,
        -35.911,
        36.071,
        -5.305,
        20.621,
        -18.518,
        -1.675
      ]
    },
    {
      "start": 12.11483,
      "duration": 0.29723,
      "confidence": 0.842,
      "loudness_start": -18.699,
      "loudness_max_time": 0.01923,
      "loudness_max": -7.472,
      "pitches": [
        0.071,
        0.056,
        0.056,
        1,
        0.305,
        0.04,
        0.025,
        0.016,
        0.018,
        0.046,
        0.45,
        0.253
      ],
      "timbre": [
        49.964,
        75.879,
        45.595,
        -4.346,
        -21.614,
        -28.29,
        -41.992,
        27.582,
        -17.885,
        18.868,
        14.208,
        -21.791
      ]
    },
    {
      "start": 12.41206,
      "duration": 0.27175,
      "confidence": 0.242,
      "loudness_start": -11.294,
      "loudness_max_time": 0.01849,
      "loudness_max": -7.995,
      "pitches": [
        0.021,
        0.021,
        0.015,
        0.123,
        0.03,
        0.01,
        0.028,
        0.122,
        1,
        0.223,
        0.014,
        0.245
      ],
      "timbre": [
        48.977,
        78.305,
        -20.299,
        10.698,
        -24.007,
        -35.635,
        -47.928,
        -10.735,
        12.901,
        -13.061,
        -27.392,
        -22.926
      ]
    },
    {
      "start": 12.68381,
      "duration": 0.27342,
      "confidence": 0.615,
      "loudness_start": -19.295,
      "loudness_max_time": 0.02427,
      "loudness_max": -10.771,
      "pitches": [
        0.035,
        0.015,
        0.091,
        0.019,
        0.019,
        0.216,
        0.035,
        0.014,
        0.038,
        0.04,
        1,
        0.088
      ],
      "timbre": [
        46.484,
        35.356,
        51.306,
        3.67,
        57.815,
        -10.015,
        -35.177,
        -15.883,
        -36.701,
        -5.751,
        8.914,
        -12.292
      ]
    },
    {
      "start": 12.95723,
      "duration": 0.31864,
      "confidence": 0.954,
      "loudness_start": -19.362,
      "loudness_max_time": 0.04368,
      "loudness_max": -5.009,
      "pitches": [
        0.097,
        0.082,
        0.099,
        0.241,
        0.162,
        0.182,
        0.098,
        0.086,
        0.195,
        0.236,
        1,
        0.161
      ],
      "timbre": [
        49.733,
        123.451,
        70.472,
        -3.685,
        57.751,
        38.633,
        -41.382,
        6.867,
        7.098,
        -45.673,
        -4.047,
        3.769
      ]
    },
    {
      "start": 13.27587,
      "duration": 0.2898,
      "confidence": 0.083,
      "loudness_start": -13.43,
      "loudness_max_time": 0.01667,
      "loudness_max": -10.163,
      "pitches": [
        0.036,
        0.013,
        0.03,
        0.103,
        0.034,
        0.185,
        0.091,
        0.15,
        0.403,
        0.141,
        1,
        0.134
      ],
      "timbre": [
        46.447,
        53.524,
        -14.983,
        24.828,
        5.64,
        -35.206,
        -46.748,
        17.384,
        -3.987,
        -6.555,
        -26.116,
        0.876
      ]
    },
    {
      "start": 13.56567,
      "duration": 0.27932,
      "confidence": 0.896,
      "loudness_start": -20.68,
      "loudness_max_time": 0.01123,
      "loudness_max": -10.557,
      "pitches": [
        0.341,
        0.024,
        0.029,
        0.138,
        0.025,
        0.03,
        0.113,
        0.048,
        0.227,
        0.046,
        0.103,
        1
      ],
      "timbre": [
        47.146,
        -5.879,
        28.877,
        17.034,
        28.219,
        -45.81,
        16.648,
        22.839,
        -4.034,
        2.771,
        -21.599,
        12.381
      ]
    },
    {
      "start": 13.84499,
      "duration": 0.2785,
      "confidence": 1,
      "loudness_start": -23.381,
      "loudness_max_time": 0.03133,
      "loudness_max": -6.492,
      "pitches": [
        0.064,
        0.228,
        0.038,
        0.181,
        0.088,
        0.293,
        1,
        0.075,
        0.079,
        0.093,
        0.164,
        0.078
      ],
      "timbre": [
        47.68,
        95.443,
        26.641,
        30.975,
        12.023,
        48.835,
        -43.647,
        -16.55,
        -15.356,
        -48.923,
        9.306,
        -5.947
      ]
    },
    {
      "start": 14.12349,
      "duration": 0.29605,
      "confidence": 0.783,
      "loudness_start": -20.088,
      "loudness_max_time": 0.08818,
      "loudness_max": -10.135,
      "pitches": [
        0.135,
        0.135,
        0.158,
        0.265,
        0.378,
        0.582,
        1,
        0.356,
        0.171,
        0.125,
        0.144,
        0.167
      ],
      "timbre": [
        46.943,
        129.271,
        65.04,
        3.573,
        14.66,
        -26.719,
        -40.135,
        80.027,
        -22.799,
        -18.042,
        15.025,
        12.868
      ]
    },
    {
      "start": 14.41955,
      "duration": 0.28943,
      "confidence": 0.935,
      "loudness_start": -16.592,
      "loudness_max_time": 0.05532,
      "loudness_max": -4.335,
      "pitches": [
        0.087,
        1,
        0.236,
        0.059,
        0.031,
        0.035,
        0.036,
        0.019,
        0.116,
        0.029,
        0.034,
        0.049
      ],
      "timbre": [
        50.482,
        97.014,
        5.485,
        25.098,
        6.774,
        11.114,
        -47.822,
        -4.539,
        6.347,
        -10.009,
        -39.546,
        -15.743
      ]
    },
    {
      "start": 14.70898,
      "duration": 0.27365,
      "confidence": 0.366,
      "loudness_start": -19.246,
      "loudness_max_time": 0.02557,
      "loudness_max": -12.358,
      "pitches": [
        0.016,
        0.281,
        0.053,
        0.02,
        0.023,
        0.125,
        1,
        0.21,
        0.026,
        0.022,
        0.024,
        0.011
      ],
      "timbre": [
        42.928,
        29.009,
        -22.485,
        18.614,
        -31.63,
        -63.636,
        -17.532,
        17.753,
        3.015,
        -23.456,
        0.407,
        1.198
      ]
    },
    {
      "start": 14.98263,
      "duration": 0.27864,
      "confidence": 0.835,
      "loudness_start": -24.418,
      "loudness_max_time": 0.1046,
      "loudness_max": -13.023,
      "pitches": [
        0.028,
        0.066,
        0.286,
        0.046,
        0.045,
        0.599,
        0.065,
        0.025,
        0.038,
        0.092,
        1,
        0.087
      ],
      "timbre": [
        44.956,
        26.485,
        95.428,
        8.94,
        90.55,
        -13.821,
        43.907,
        13.933,
        6.996,
        -4.423,
        -3.225,
        8.146
      ]
    },
    {
      "start": 15.26127,
      "duration": 0.29637,
      "confidence": 1,
      "loudness_start": -20.155,
      "loudness_max_time": 0.06226,
      "loudness_max": -5.068,
      "pitches": [
        0.055,
        0.101,
        0.064,
        0.056,
        0.086,
        0.137,
        0.094,
        0.062,
        0.083,
        0.103,
        1,
        0.105
      ],
      "timbre": [
        50.436,
        134.709,
        59.557,
        -1.672,
        36.34,
        43.77,
        -42.458,
        -7.242,
        -0.499,
        -16.644,
        1.386,
        -5.018
      ]
    },
    {
      "start": 15.55764,
      "duration": 0.59746,
      "confidence": 0.23,
      "loudness_start": -12.272,
      "loudness_max_time": 0.03311,
      "loudness_max": -8.725,
      "pitches": [
        0.733,
        1,
        0.241,
        0.271,
        0.131,
        0.094,
        0.078,
        0.125,
        0.445,
        0.159,
        0.076,
        0.208
      ],
      "timbre": [
        47.228,
        42.136,
        2.827,
        49.479,
        9.821,
        -19.067,
        -27.929,
        20.618,
        -5.779,
        15.019,
        -39.623,
        6.935
      ]
    },
    {
      "start": 16.1551,
      "duration": 0.2673,
      "confidence": 1,
      "loudness_start": -24.227,
      "loudness_max_time": 0.07134,
      "loudness_max": -5.735,
      "pitches": [
        0.155,
        0.76,
        0.516,
        0.17,
        0.112,
        0.272,
        0.951,
        0.567,
        0.192,
        0.182,
        1,
        0.272
      ],
      "timbre": [
        49.793,
        133.194,
        78.629,
        51.767,
        68.162,
        1.726,
        7.612,
        -22.803,
        19.541,
        20.456,
        -15.837,
        27.256
      ]
    },
    {
      "start": 16.4224,
      "duration": 0.30231,
      "confidence": 0.75,
      "loudness_start": -15.057,
      "loudness_max_time": 0.03782,
      "loudness_max": -6.006,
      "pitches": [
        0.126,
        0.412,
        0.101,
        0.176,
        0.208,
        0.355,
        1,
        0.151,
        0.112,
        0.074,
        0.115,
        0.083
      ],
      "timbre": [
        50.134,
        126.249,
        44.565,
        21.792,
        0.575,
        8.449,
        -21.273,
        7.732,
        -6.054,
        -13.649,
        -9.858,
        3.575
      ]
    },
    {
      "start": 16.72472,
      "duration": 0.2439,
      "confidence": 0.491,
      "loudness_start": -18.065,
      "loudness_max_time": 0.00232,
      "loudness_max": -9.273,
      "pitches": [
        0.025,
        0.019,
        0.092,
        1,
        0.344,
        0.028,
        0.02,
        0.019,
        0.324,
        0.214,
        0.099,
        0.03
      ],
      "timbre": [
        47.1,
        30.701,
        32.838,
        1.882,
        -1.869,
        -54.526,
        -14.901,
        -26.46,
        -2.914,
        30.118,
        -31.537,
        10.381
      ]
    },
    {
      "start": 16.96862,
      "duration": 0.30109,
      "confidence": 0.638,
      "loudness_start": -15.349,
      "loudness_max_time": 0.0574,
      "loudness_max": -7.254,
      "pitches": [
        0.068,
        0.102,
        0.114,
        0.375,
        0.191,
        0.149,
        0.136,
        0.158,
        1,
        0.145,
        0.046,
        0.066
      ],
      "timbre": [
        46.26,
        -7.649,
        -2.008,
        16.928,
        35.22,
        -14.514,
        -0.274,
        22.462,
        -4.364,
        14.217,
        -44.26,
        -6.937
      ]
    },
    {
      "start": 17.26971,
      "duration": 0.19156,
      "confidence": 0.797,
      "loudness_start": -21.906,
      "loudness_max_time": 0.10076,
      "loudness_max": -13.024,
      "pitches": [
        0.093,
        0.104,
        0.175,
        1,
        0.234,
        0.08,
        0.074,
        0.106,
        0.085,
        0.077,
        0.217,
        0.118
      ],
      "timbre": [
        43.601,
        56.941,
        35.452,
        -64.33,
        37.334,
        3.651,
        -6.021,
        -18.42,
        -0.017,
        -0.057,
        -3.567,
        -36.445
      ]
    },
    {
      "start": 17.46127,
      "duration": 0.09882,
      "confidence": 0.426,
      "loudness_start": -15.712,
      "loudness_max_time": 0.01073,
      "loudness_max": -10.524,
      "pitches": [
        0.552,
        1,
        0.162,
        0.433,
        0.282,
        0.059,
        0.078,
        0.094,
        0.136,
        0.141,
        0.326,
        0.106
      ],
      "timbre": [
        47.182,
        36.008,
        28.655,
        -9.273,
        -4.049,
        -58.193,
        -14.014,
        9.729,
        8.331,
        9.664,
        -4.25,
        -42.835
      ]
    },
    {
      "start": 17.56009,
      "duration": 0.27274,
      "confidence": 0.803,
      "loudness_start": -14.574,
      "loudness_max_time": 0.05924,
      "loudness_max": -4.584,
      "pitches": [
        0.323,
        0.408,
        0.709,
        1,
        0.697,
        0.403,
        0.502,
        0.183,
        0.317,
        0.345,
        0.388,
        0.341
      ],
      "timbre": [
        50.037,
        147.389,
        31.327,
        7.363,
        0.191,
        3.686,
        -19.221,
        44.12,
        19.508,
        -17.777,
        -18.234,
        -3.634
      ]
    },
    {
      "start": 17.83283,
      "duration": 0.20295,
      "confidence": 0.635,
      "loudness_start": -18.053,
      "loudness_max_time": 0.05525,
      "loudness_max": -9.49,
      "pitches": [
        0.087,
        0.053,
        0.059,
        0.068,
        0.071,
        0.384,
        0.139,
        0.08,
        0.098,
        0.304,
        1,
        0.334
      ],
      "timbre": [
        46.024,
        129.194,
        25.808,
        9.932,
        -8.339,
        2.614,
        -9.821,
        -18.806,
        -16.966,
        41.731,
        -18.509,
        10.457
      ]
    },
    {
      "start": 18.03578,
      "duration": 0.12195,
      "confidence": 0.356,
      "loudness_start": -17.189,
      "loudness_max_time": 0.01104,
      "loudness_max": -11.256,
      "pitches": [
        0.728,
        1,
        0.129,
        0.055,
        0.058,
        0.107,
        0.09,
        0.057,
        0.179,
        0.192,
        0.44,
        0.427
      ],
      "timbre": [
        43.633,
        60.834,
        -39.38,
        21.605,
        -25.799,
        -72.787,
        -7.274,
        18.126,
        23.455,
        -19.556,
        -3.006,
        7.36
      ]
    },
    {
      "start": 18.15773,
      "duration": 0.28472,
      "confidence": 0.81,
      "loudness_start": -22.132,
      "loudness_max_time": 0.01228,
      "loudness_max": -7.722,
      "pitches": [
        0.249,
        0.125,
        0.105,
        0.224,
        0.165,
        0.111,
        0.245,
        0.078,
        0.103,
        0.086,
        0.149,
        1
      ],
      "timbre": [
        43.987,
        34.521,
        -32.471,
        55.525,
        -21.297,
        -102.007,
        -23.971,
        32.994,
        9.562,
        7.634,
        -6.608,
        7.578
      ]
    },
    {
      "start": 18.44245,
      "duration": 0.15093,
      "confidence": 0.999,
      "loudness_start": -24.478,
      "loudness_max_time": 0.02038,
      "loudness_max": -9.332,
      "pitches": [
        0.488,
        0.583,
        0.324,
        1,
        0.5,
        0.44,
        0.465,
        0.355,
        0.408,
        0.506,
        0.861,
        0.51
      ],
      "timbre": [
        45.656,
        203.621,
        51.696,
        46.942,
        27.463,
        28.642,
        -37.804,
        -8.501,
        25.105,
        -0.562,
        8.17,
        -16.472
      ]
    },
    {
      "start": 18.59338,
      "duration": 0.12807,
      "confidence": 0.748,
      "loudness_start": -20.321,
      "loudness_max_time": 0.02573,
      "loudness_max": -10.394,
      "pitches": [
        0.857,
        1,
        0.418,
        0.169,
        0.204,
        0.154,
        0.294,
        0.355,
        0.318,
        0.21,
        0.303,
        0.572
      ],
      "timbre": [
        46.423,
        41.187,
        -13.098,
        -19.362,
        22.719,
        -17.907,
        -31.602,
        -17.543,
        8.612,
        59.773,
        9.28,
        10.814
      ]
    },
    {
      "start": 18.72145,
      "duration": 0.30721,
      "confidence": 0.945,
      "loudness_start": -14.78,
      "loudness_max_time": 0.02705,
      "loudness_max": -2.501,
      "pitches": [
        0.147,
        0.316,
        0.36,
        0.178,
        0.272,
        0.249,
        0.997,
        1,
        0.296,
        0.206,
        0.297,
        0.188
      ],
      "timbre": [
        52.319,
        61.963,
        0.416,
        28.389,
        70.296,
        -4.835,
        -12.132,
        43.47,
        9.192,
        -9.192,
        13.007,
        -0.082
      ]
    },
    {
      "start": 19.02866,
      "duration": 0.16417,
      "confidence": 0.804,
      "loudness_start": -18.704,
      "loudness_max_time": 0.04171,
      "loudness_max": -6.913,
      "pitches": [
        0.196,
        1,
        0.384,
        0.052,
        0.027,
        0.056,
        0.132,
        0.17,
        0.342,
        0.085,
        0.049,
        0.032
      ],
      "timbre": [
        46.724,
        79.074,
        -44.161,
        71.857,
        3.302,
        -4.862,
        -16.468,
        24.274,
        -15.149,
        -1.864,
        -11.261,
        16.099
      ]
    },
    {
      "start": 19.19283,
      "duration": 0.12014,
      "confidence": 1,
      "loudness_start": -22.041,
      "loudness_max_time": 0.01779,
      "loudness_max": -6.406,
      "pitches": [
        0.307,
        0.91,
        0.543,
        1,
        0.435,
        0.225,
        0.624,
        0.751,
        0.409,
        0.302,
        0.277,
        0.117
      ],
      "timbre": [
        50.651,
        71.377,
        -37.879,
        -14.574,
        -5.345,
        -17.792,
        -39.217,
        20.296,
        -6.99,
        -16.824,
        14.318,
        -16.693
      ]
    },
    {
      "start": 19.31297,
      "duration": 0.30204,
      "confidence": 0.409,
      "loudness_start": -13.25,
      "loudness_max_time": 0.01776,
      "loudness_max": -6.585,
      "pitches": [
        0.246,
        0.459,
        0.302,
        0.142,
        0.066,
        0.205,
        1,
        0.278,
        0.079,
        0.037,
        0.051,
        0.206
      ],
      "timbre": [
        50.844,
        89.128,
        -50.706,
        -21.143,
        -18.947,
        -48.763,
        -33.851,
        31.562,
        -4.004,
        12.735,
        -13.111,
        -19.494
      ]
    },
    {
      "start": 19.61501,
      "duration": 0.25546,
      "confidence": 0.671,
      "loudness_start": -13.875,
      "loudness_max_time": 0.04171,
      "loudness_max": -6.913,
      "pitches": [
        0.168,
        0.287,
        0.333,
        0.158,
        0.296,
        0.292,
        1,
        0.737,
        0.421,
        0.263,
        0.823,
        0.279
      ],
      "timbre": [
        49.799,
        102.54,
        42.314,
        25.208,
        73.715,
        -11.978,
        -19.821,
        22.396,
        -12.151,
        31.541,
        -17.417,
        -8.038
      ]
    },
    {
      "start": 19.87048,
      "duration": 0.30181,
      "confidence": 1,
      "loudness_start": -18.351,
      "loudness_max_time": 0.04519,
      "loudness_max": -3.856,
      "pitches": [
        0.146,
        0.309,
        0.152,
        0.214,
        0.311,
        0.271,
        1,
        0.751,
        0.33,
        0.204,
        0.273,
        0.185
      ],
      "timbre": [
        51.688,
        91.286,
        15.258,
        16.084,
        35.057,
        15.358,
        -20.515,
        10.678,
        -12.141,
        29.141,
        5.213,
        5.164
      ]
    },
    {
      "start": 20.17229,
      "duration": 0.14014,
      "confidence": 0.565,
      "loudness_start": -13.856,
      "loudness_max_time": 0.01618,
      "loudness_max": -6.319,
      "pitches": [
        1,
        0.654,
        0.037,
        0.034,
        0.032,
        0.039,
        0.139,
        0.099,
        0.072,
        0.045,
        0.385,
        0.09
      ],
      "timbre": [
        49.802,
        54.149,
        -26.931,
        22.921,
        -6.91,
        -44.691,
        -24.51,
        1.413,
        -36.421,
        -1.552,
        -22.255,
        -9.964
      ]
    },
    {
      "start": 20.31243,
      "duration": 0.12073,
      "confidence": 0.508,
      "loudness_start": -15.589,
      "loudness_max_time": 0.03044,
      "loudness_max": -9.462,
      "pitches": [
        1,
        0.557,
        0.051,
        0.032,
        0.064,
        0.198,
        0.205,
        0.095,
        0.212,
        0.216,
        0.542,
        0.129
      ],
      "timbre": [
        47.81,
        34.193,
        -38.818,
        -3.63,
        3.419,
        -24.464,
        -44.985,
        4.621,
        -17.852,
        -3.293,
        -25.53,
        -28.706
      ]
    },
    {
      "start": 20.43315,
      "duration": 0.30209,
      "confidence": 0.751,
      "loudness_start": -16.573,
      "loudness_max_time": 0.02287,
      "loudness_max": -6.625,
      "pitches": [
        0.227,
        1,
        0.665,
        0.201,
        0.12,
        0.107,
        0.227,
        0.081,
        0.076,
        0.029,
        0.052,
        0.144
      ],
      "timbre": [
        48.314,
        35.4,
        -56.685,
        30.252,
        -3.238,
        -14.287,
        -19.418,
        38.82,
        -11.177,
        27.587,
        -13.124,
        -10.099
      ]
    },
    {
      "start": 20.73524,
      "duration": 0.24404,
      "confidence": 0.99,
      "loudness_start": -20.432,
      "loudness_max_time": 0.07056,
      "loudness_max": -6.135,
      "pitches": [
        0.73,
        0.77,
        0.822,
        0.628,
        0.518,
        0.303,
        0.712,
        0.49,
        0.227,
        0.198,
        0.437,
        1
      ],
      "timbre": [
        49.452,
        30.069,
        -5.677,
        37.338,
        13.846,
        -26.624,
        -14.545,
        -0.321,
        20.151,
        33.444,
        -31.56,
        -21.447
      ]
    },
    {
      "start": 20.97927,
      "duration": 0.3366,
      "confidence": 1,
      "loudness_start": -20.892,
      "loudness_max_time": 0.10137,
      "loudness_max": -2.743,
      "pitches": [
        0.143,
        0.28,
        0.159,
        0.197,
        0.211,
        0.312,
        1,
        0.661,
        0.423,
        0.175,
        0.194,
        0.134
      ],
      "timbre": [
        47.973,
        109.364,
        35.981,
        -62.201,
        25.055,
        32.53,
        -4.917,
        -16.854,
        -21.992,
        34.804,
        -43.515,
        3.977
      ]
    },
    {
      "start": 21.31587,
      "duration": 0.25324,
      "confidence": 0.616,
      "loudness_start": -17.547,
      "loudness_max_time": 0.02531,
      "loudness_max": -7.208,
      "pitches": [
        0.022,
        0.026,
        0.107,
        1,
        0.52,
        0.034,
        0.024,
        0.017,
        0.02,
        0.022,
        0.034,
        0.021
      ],
      "timbre": [
        46.982,
        79.222,
        -31.298,
        68.984,
        -23.118,
        -39.256,
        -0.636,
        -15.784,
        -31.338,
        11.125,
        -10.025,
        13.916
      ]
    },
    {
      "start": 21.56912,
      "duration": 0.29832,
      "confidence": 1,
      "loudness_start": -22.242,
      "loudness_max_time": 0.05005,
      "loudness_max": -7.69,
      "pitches": [
        0.135,
        0.185,
        0.199,
        0.146,
        0.107,
        0.094,
        0.127,
        0.259,
        1,
        0.261,
        0.063,
        0.179
      ],
      "timbre": [
        45.763,
        15.627,
        -55.443,
        -20.913,
        -11.684,
        65.062,
        3.104,
        5.979,
        -12.85,
        26.212,
        -52.177,
        -13.807
      ]
    },
    {
      "start": 21.86744,
      "duration": 0.16717,
      "confidence": 0.954,
      "loudness_start": -24.344,
      "loudness_max_time": 0.05244,
      "loudness_max": -10.314,
      "pitches": [
        0.045,
        0.074,
        0.07,
        0.084,
        0.083,
        0.164,
        0.293,
        1,
        0.28,
        0.078,
        0.065,
        0.043
      ],
      "timbre": [
        46.033,
        120.969,
        -56.489,
        -42.449,
        -2.171,
        27.729,
        -18.215,
        -57.942,
        -37.618,
        -0.157,
        -44.046,
        -7.72
      ]
    },
    {
      "start": 22.0346,
      "duration": 0.10553,
      "confidence": 0.562,
      "loudness_start": -22.735,
      "loudness_max_time": 0.02124,
      "loudness_max": -8.622,
      "pitches": [
        0.061,
        0.036,
        0.055,
        0.122,
        0.278,
        1,
        0.506,
        0.064,
        0.021,
        0.023,
        0.017,
        0.037
      ],
      "timbre": [
        45.091,
        13.676,
        -26.929,
        39.278,
        23.866,
        -34.824,
        -50.783,
        -23.174,
        -8.574,
        38.564,
        15.44,
        18.887
      ]
    },
    {
      "start": 22.14014,
      "duration": 0.31937,
      "confidence": 1,
      "loudness_start": -19.795,
      "loudness_max_time": 0.06049,
      "loudness_max": -2.443,
      "pitches": [
        0.063,
        0.098,
        0.052,
        0.082,
        0.06,
        0.102,
        1,
        0.363,
        0.109,
        0.104,
        0.121,
        0.074
      ],
      "timbre": [
        49.247,
        63.198,
        -6.593,
        -46.453,
        51.172,
        64.749,
        -36.522,
        6.848,
        25.799,
        -12.805,
        -18.046,
        17.512
      ]
    },
    {
      "start": 22.4595,
      "duration": 0.11669,
      "confidence": 0.765,
      "loudness_start": -16.524,
      "loudness_max_time": 0.03104,
      "loudness_max": -6.88,
      "pitches": [
        0.694,
        0.36,
        0.292,
        0.143,
        0.274,
        0.423,
        0.782,
        0.791,
        0.879,
        0.853,
        1,
        0.35
      ],
      "timbre": [
        50.294,
        70.896,
        -11.142,
        0.953,
        24.191,
        -12.321,
        -23.525,
        -11.537,
        -27.19,
        -0.002,
        -7.95,
        -22.578
      ]
    },
    {
      "start": 22.57619,
      "duration": 0.17932,
      "confidence": 0.249,
      "loudness_start": -14.226,
      "loudness_max_time": 0.0126,
      "loudness_max": -8.386,
      "pitches": [
        0.472,
        0.223,
        0.042,
        0.06,
        0.111,
        0.235,
        0.171,
        0.098,
        0.518,
        0.536,
        1,
        0.158
      ],
      "timbre": [
        49.713,
        19.193,
        28.381,
        10.671,
        -0.177,
        -39.379,
        12.703,
        33.198,
        0.477,
        21.119,
        -28.575,
        5.63
      ]
    },
    {
      "start": 22.75551,
      "duration": 0.12762,
      "confidence": 0.627,
      "loudness_start": -13.758,
      "loudness_max_time": 0.01596,
      "loudness_max": -6.203,
      "pitches": [
        0.949,
        1,
        0.025,
        0.049,
        0.083,
        0.114,
        0.407,
        0.324,
        0.503,
        0.501,
        0.481,
        0.26
      ],
      "timbre": [
        48.384,
        47.137,
        -78.249,
        38.976,
        -13.948,
        -60.29,
        -35.861,
        27.639,
        -13.086,
        -5.128,
        -24.394,
        -8.272
      ]
    },
    {
      "start": 22.88313,
      "duration": 0.10517,
      "confidence": 0.54,
      "loudness_start": -20.511,
      "loudness_max_time": 0.02221,
      "loudness_max": -10.292,
      "pitches": [
        1,
        0.567,
        0.046,
        0.038,
        0.064,
        0.088,
        0.33,
        0.273,
        0.396,
        0.353,
        0.682,
        0.304
      ],
      "timbre": [
        43.911,
        18.418,
        -73.413,
        38.851,
        1.643,
        -29.487,
        -42.078,
        6.11,
        -15.651,
        11.221,
        -16.724,
        -7.638
      ]
    },
    {
      "start": 22.9883,
      "duration": 0.32844,
      "confidence": 1,
      "loudness_start": -24.491,
      "loudness_max_time": 0.07651,
      "loudness_max": -5.531,
      "pitches": [
        0.471,
        0.895,
        1,
        0.374,
        0.363,
        0.417,
        0.564,
        0.429,
        0.173,
        0.08,
        0.219,
        0.568
      ],
      "timbre": [
        46.55,
        38.656,
        12.726,
        -76.422,
        41.44,
        -1.73,
        26.802,
        9.903,
        6.454,
        16.367,
        -13.704,
        9.279
      ]
    },
    {
      "start": 23.31673,
      "duration": 0.30857,
      "confidence": 0.999,
      "loudness_start": -16.14,
      "loudness_max_time": 0.03143,
      "loudness_max": -1.899,
      "pitches": [
        0.162,
        0.198,
        0.243,
        0.197,
        0.186,
        0.416,
        0.677,
        0.759,
        0.537,
        1,
        0.985,
        0.503
      ],
      "timbre": [
        51.885,
        26.533,
        14,
        37.449,
        35.879,
        5.466,
        -3.824,
        14.101,
        -14.267,
        -6.354,
        36.835,
        1.06
      ]
    },
    {
      "start": 23.62531,
      "duration": 0.28544,
      "confidence": 0.59,
      "loudness_start": -12.843,
      "loudness_max_time": 0.02756,
      "loudness_max": -6.073,
      "pitches": [
        0.085,
        1,
        0.395,
        0.089,
        0.069,
        0.061,
        0.056,
        0.05,
        0.063,
        0.052,
        0.038,
        0.053
      ],
      "timbre": [
        49.393,
        107.054,
        -36.41,
        39.312,
        -13.609,
        -31.709,
        -22.802,
        -2.508,
        -4.922,
        3.171,
        -26.323,
        1.237
      ]
    },
    {
      "start": 23.91075,
      "duration": 0.24345,
      "confidence": 0.953,
      "loudness_start": -19.411,
      "loudness_max_time": 0.01113,
      "loudness_max": -5.901,
      "pitches": [
        0.085,
        0.338,
        0.259,
        0.157,
        0.118,
        0.218,
        1,
        0.418,
        0.166,
        0.07,
        0.06,
        0.167
      ],
      "timbre": [
        50.295,
        25.754,
        -39.68,
        3.66,
        -19.552,
        -55.464,
        -33.973,
        -13.42,
        -25.708,
        1.795,
        -19.998,
        -36.356
      ]
    },
    {
      "start": 24.1542,
      "duration": 0.30812,
      "confidence": 0.834,
      "loudness_start": -16.025,
      "loudness_max_time": 0.08428,
      "loudness_max": -6.357,
      "pitches": [
        0.295,
        1,
        0.349,
        0.079,
        0.055,
        0.089,
        0.044,
        0.086,
        0.22,
        0.138,
        0.091,
        0.26
      ],
      "timbre": [
        46.243,
        80.796,
        -14.06,
        -41.73,
        44.012,
        6.758,
        -40.772,
        36.508,
        4.577,
        -3.467,
        -54.444,
        -6.105
      ]
    },
    {
      "start": 24.46231,
      "duration": 0.2961,
      "confidence": 1,
      "loudness_start": -23.832,
      "loudness_max_time": 0.05857,
      "loudness_max": -3.563,
      "pitches": [
        0.433,
        0.338,
        0.166,
        0.155,
        0.132,
        0.159,
        0.345,
        0.421,
        0.327,
        0.272,
        0.412,
        1
      ],
      "timbre": [
        49.415,
        123.658,
        6.598,
        11.372,
        59.602,
        58.355,
        -34.36,
        33.647,
        -16.062,
        53.391,
        -3.369,
        0.627
      ]
    },
    {
      "start": 24.75841,
      "duration": 0.18122,
      "confidence": 1,
      "loudness_start": -20.011,
      "loudness_max_time": 0.03711,
      "loudness_max": -5.623,
      "pitches": [
        1,
        0.487,
        0.053,
        0.04,
        0.047,
        0.078,
        0.052,
        0.129,
        0.082,
        0.078,
        0.357,
        0.14
      ],
      "timbre": [
        48.746,
        68.934,
        -14.295,
        26.246,
        36.523,
        32.683,
        3.397,
        -6.016,
        -32.09,
        46.415,
        -6.548,
        5.086
      ]
    },
    {
      "start": 24.93964,
      "duration": 0.11379,
      "confidence": 0.679,
      "loudness_start": -18.226,
      "loudness_max_time": 0.01536,
      "loudness_max": -8.836,
      "pitches": [
        1,
        0.781,
        0.126,
        0.088,
        0.144,
        0.109,
        0.31,
        0.42,
        0.429,
        0.242,
        0.377,
        0.26
      ],
      "timbre": [
        49.195,
        14.599,
        -7.401,
        -13.92,
        17.299,
        -33.518,
        -33.747,
        -0.665,
        -10.296,
        7.417,
        -4.863,
        8.857
      ]
    },
    {
      "start": 25.05342,
      "duration": 0.26236,
      "confidence": 0.376,
      "loudness_start": -13.898,
      "loudness_max_time": 0.01581,
      "loudness_max": -7.432,
      "pitches": [
        0.15,
        1,
        0.634,
        0.098,
        0.096,
        0.043,
        0.067,
        0.057,
        0.229,
        0.043,
        0.026,
        0.079
      ],
      "timbre": [
        47.504,
        14.753,
        -72.45,
        49.282,
        -1.892,
        -38.965,
        -31.557,
        23.454,
        -17.796,
        -14.992,
        -57.107,
        -5.726
      ]
    },
    {
      "start": 25.31578,
      "duration": 0.30748,
      "confidence": 1,
      "loudness_start": -25.612,
      "loudness_max_time": 0.05217,
      "loudness_max": -4.64,
      "pitches": [
        0.501,
        0.97,
        1,
        0.944,
        0.651,
        0.335,
        0.508,
        0.191,
        0.406,
        0.178,
        0.316,
        0.586
      ],
      "timbre": [
        46.095,
        35.587,
        -27.567,
        5.587,
        35.832,
        94.606,
        -0.987,
        62.995,
        41.937,
        25.779,
        -8.828,
        -17.014
      ]
    },
    {
      "start": 25.62327,
      "duration": 0.29587,
      "confidence": 1,
      "loudness_start": -24.392,
      "loudness_max_time": 0.02302,
      "loudness_max": -2.62,
      "pitches": [
        0.565,
        0.225,
        0.171,
        0.683,
        0.263,
        0.414,
        0.577,
        0.51,
        1,
        0.289,
        0.316,
        0.225
      ],
      "timbre": [
        52.007,
        64.756,
        14.711,
        57.464,
        38.788,
        14.116,
        -11.231,
        36.864,
        4.836,
        -5.344,
        8.9,
        10.27
      ]
    },
    {
      "start": 25.91914,
      "duration": 0.14367,
      "confidence": 0.765,
      "loudness_start": -16.614,
      "loudness_max_time": 0.02015,
      "loudness_max": -7.21,
      "pitches": [
        0.08,
        1,
        0.1,
        0.577,
        0.274,
        0.077,
        0.054,
        0.056,
        0.071,
        0.078,
        0.152,
        0.037
      ],
      "timbre": [
        46.571,
        96.697,
        -52.483,
        54.691,
        -16.943,
        -46.021,
        -0.729,
        -0.134,
        -27.379,
        8.826,
        -19.276,
        7.753
      ]
    },
    {
      "start": 26.06281,
      "duration": 0.13311,
      "confidence": 0.767,
      "loudness_start": -21.728,
      "loudness_max_time": 0.04545,
      "loudness_max": -11.584,
      "pitches": [
        0.3,
        1,
        0.057,
        0.194,
        0.27,
        0.251,
        0.262,
        0.175,
        0.22,
        0.216,
        0.209,
        0.065
      ],
      "timbre": [
        43.403,
        -2.393,
        -43.962,
        4.313,
        -37.244,
        20.561,
        -17.814,
        17.439,
        -24.457,
        29.678,
        -0.485,
        -4.908
      ]
    },
    {
      "start": 26.19592,
      "duration": 0.29723,
      "confidence": 0.93,
      "loudness_start": -21.588,
      "loudness_max_time": 0.02331,
      "loudness_max": -8.188,
      "pitches": [
        0.15,
        0.135,
        0.12,
        0.145,
        0.067,
        0.034,
        0.06,
        0.079,
        1,
        0.272,
        0.147,
        0.223
      ],
      "timbre": [
        48.717,
        -0.253,
        -51.144,
        8.702,
        -10.648,
        -34.148,
        -8.9,
        4.584,
        -15.137,
        10.819,
        -26.621,
        -20.171
      ]
    },
    {
      "start": 26.49315,
      "duration": 0.23297,
      "confidence": 0.941,
      "loudness_start": -23.077,
      "loudness_max_time": 0.03454,
      "loudness_max": -8.364,
      "pitches": [
        0.168,
        0.138,
        0.063,
        0.183,
        0.35,
        1,
        0.47,
        0.133,
        0.097,
        0.093,
        0.094,
        0.103
      ],
      "timbre": [
        45.522,
        123.91,
        -52.282,
        62.339,
        33.715,
        -1.906,
        -71.767,
        35.214,
        -43.054,
        11.515,
        -38.632,
        -16.295
      ]
    },
    {
      "start": 26.72612,
      "duration": 0.31361,
      "confidence": 1,
      "loudness_start": -26.229,
      "loudness_max_time": 0.0801,
      "loudness_max": -1.136,
      "pitches": [
        0.3,
        0.41,
        0.259,
        0.355,
        0.471,
        0.38,
        0.926,
        1,
        0.602,
        0.373,
        0.749,
        0.364
      ],
      "timbre": [
        45.615,
        110.457,
        57.005,
        -108.519,
        66.364,
        75.363,
        -4.61,
        -12.806,
        -20.877,
        75.683,
        -30.981,
        25.073
      ]
    },
    {
      "start": 27.03973,
      "duration": 0.14925,
      "confidence": 0.917,
      "loudness_start": -18.981,
      "loudness_max_time": 0.04615,
      "loudness_max": -6.19,
      "pitches": [
        0.692,
        0.378,
        0.252,
        0.289,
        0.285,
        0.384,
        0.441,
        0.427,
        0.797,
        0.766,
        1,
        0.43
      ],
      "timbre": [
        47.765,
        98.327,
        -19.755,
        -3.272,
        23.956,
        23.224,
        -4.162,
        17.518,
        -20.182,
        40.918,
        -23.084,
        2.919
      ]
    },
    {
      "start": 27.18898,
      "duration": 0.13528,
      "confidence": 0.672,
      "loudness_start": -15.993,
      "loudness_max_time": 0.06312,
      "loudness_max": -8.792,
      "pitches": [
        0.945,
        0.568,
        0.168,
        0.15,
        0.148,
        0.177,
        0.323,
        0.348,
        0.807,
        0.783,
        1,
        0.423
      ],
      "timbre": [
        48.075,
        48.128,
        -15.614,
        -26.589,
        -11.813,
        9.713,
        -22.308,
        -1.006,
        -33.48,
        38.311,
        -36.101,
        -16.301
      ]
    },
    {
      "start": 27.32426,
      "duration": 0.25905,
      "confidence": 0.717,
      "loudness_start": -15.924,
      "loudness_max_time": 0.04607,
      "loudness_max": -7.613,
      "pitches": [
        0.783,
        0.319,
        0.267,
        0.08,
        0.091,
        0.133,
        0.166,
        0.074,
        0.055,
        0.018,
        0.048,
        1
      ],
      "timbre": [
        47.772,
        31.879,
        -44.47,
        6.152,
        -3.909,
        20.742,
        -10.708,
        8.819,
        -2.411,
        17.609,
        -42.573,
        -31.524
      ]
    },
    {
      "start": 27.58331,
      "duration": 0.298,
      "confidence": 1,
      "loudness_start": -22.83,
      "loudness_max_time": 0.07753,
      "loudness_max": -5.322,
      "pitches": [
        0.848,
        1,
        0.77,
        0.34,
        0.667,
        0.575,
        0.91,
        0.283,
        0.128,
        0.108,
        0.308,
        0.921
      ],
      "timbre": [
        44.824,
        109.355,
        -36.002,
        -69.045,
        -3.816,
        65.441,
        -34.969,
        21.174,
        0.942,
        13.449,
        -54.158,
        -13.002
      ]
    },
    {
      "start": 27.88132,
      "duration": 0.34259,
      "confidence": 1,
      "loudness_start": -21.825,
      "loudness_max_time": 0.06535,
      "loudness_max": -2.904,
      "pitches": [
        0.659,
        0.816,
        0.7,
        0.883,
        0.413,
        0.285,
        0.64,
        1,
        0.524,
        0.54,
        0.524,
        0.287
      ],
      "timbre": [
        47.588,
        61.294,
        23.042,
        -49.905,
        29.394,
        61.649,
        5.828,
        -7.139,
        -27.385,
        16.694,
        -22.577,
        4.149
      ]
    },
    {
      "start": 28.2239,
      "duration": 0.27778,
      "confidence": 0.795,
      "loudness_start": -18.737,
      "loudness_max_time": 0.01818,
      "loudness_max": -6.786,
      "pitches": [
        0.101,
        1,
        0.485,
        0.1,
        0.086,
        0.055,
        0.038,
        0.056,
        0.078,
        0.057,
        0.069,
        0.069
      ],
      "timbre": [
        48.672,
        125.959,
        -36.685,
        41.716,
        -16.671,
        -41.073,
        -27.697,
        -0.872,
        -22.802,
        11.459,
        -29.028,
        -1.738
      ]
    },
    {
      "start": 28.50168,
      "duration": 0.16871,
      "confidence": 0.929,
      "loudness_start": -19.982,
      "loudness_max_time": 0.02791,
      "loudness_max": -6.649,
      "pitches": [
        0.675,
        1,
        0.103,
        0.047,
        0.31,
        0.311,
        0.393,
        0.295,
        0.564,
        0.68,
        0.899,
        0.059
      ],
      "timbre": [
        49.833,
        -4.115,
        -51.975,
        9.181,
        29.614,
        -29.922,
        1.126,
        -12.405,
        -1.013,
        36.642,
        -20.705,
        1.056
      ]
    },
    {
      "start": 28.67039,
      "duration": 0.24426,
      "confidence": 0.781,
      "loudness_start": -17.361,
      "loudness_max_time": 0.06306,
      "loudness_max": -7.823,
      "pitches": [
        0.269,
        0.686,
        0.229,
        0.063,
        0.096,
        0.426,
        1,
        0.717,
        0.297,
        0.09,
        0.084,
        0.097
      ],
      "timbre": [
        48.34,
        43.466,
        -8.628,
        11.871,
        39.033,
        1.162,
        9.199,
        73.7,
        9.552,
        12.985,
        -14.094,
        4.603
      ]
    },
    {
      "start": 28.91465,
      "duration": 0.14508,
      "confidence": 0.932,
      "loudness_start": -23.522,
      "loudness_max_time": 0.05321,
      "loudness_max": -10.908,
      "pitches": [
        0.206,
        0.183,
        0.102,
        0.216,
        0.391,
        0.57,
        0.303,
        0.414,
        1,
        0.988,
        0.699,
        0.628
      ],
      "timbre": [
        42.253,
        97.475,
        -51.098,
        53.283,
        9.13,
        42.707,
        -22.875,
        -17.107,
        -42.724,
        15.914,
        -27.42,
        10.675
      ]
    },
    {
      "start": 29.05973,
      "duration": 0.30195,
      "confidence": 1,
      "loudness_start": -29.264,
      "loudness_max_time": 0.03738,
      "loudness_max": -2.159,
      "pitches": [
        0.159,
        0.351,
        0.702,
        1,
        0.173,
        0.151,
        0.349,
        0.291,
        0.239,
        0.172,
        0.206,
        0.146
      ],
      "timbre": [
        50.113,
        129.942,
        -1.57,
        13.624,
        52.743,
        63.505,
        -20.683,
        27.886,
        -36.617,
        51.013,
        -6.917,
        8.002
      ]
    },
    {
      "start": 29.36168,
      "duration": 0.1532,
      "confidence": 1,
      "loudness_start": -20.783,
      "loudness_max_time": 0.04573,
      "loudness_max": -5.415,
      "pitches": [
        1,
        0.615,
        0.06,
        0.051,
        0.072,
        0.062,
        0.077,
        0.155,
        0.178,
        0.227,
        0.552,
        0.127
      ],
      "timbre": [
        50.481,
        39.594,
        -17.843,
        32.484,
        55.318,
        -4.286,
        0.13,
        -10.76,
        -21.59,
        17.629,
        -17.396,
        16.705
      ]
    },
    {
      "start": 29.51488,
      "duration": 0.25261,
      "confidence": 0.716,
      "loudness_start": -16.256,
      "loudness_max_time": 0.14842,
      "loudness_max": -5.907,
      "pitches": [
        0.972,
        1,
        0.525,
        0.241,
        0.303,
        0.375,
        0.383,
        0.244,
        0.194,
        0.181,
        0.22,
        0.593
      ],
      "timbre": [
        48.813,
        21.606,
        6.333,
        -32.677,
        31.239,
        -0.48,
        28.494,
        38.169,
        0.89,
        19.293,
        -24.355,
        9.457
      ]
    },
    {
      "start": 29.76748,
      "duration": 0.1746,
      "confidence": 0.69,
      "loudness_start": -18.406,
      "loudness_max_time": 0.03595,
      "loudness_max": -8.982,
      "pitches": [
        0.647,
        1,
        0.118,
        0.03,
        0.035,
        0.037,
        0.069,
        0.075,
        0.115,
        0.154,
        0.174,
        0.051
      ],
      "timbre": [
        44.907,
        129.18,
        -90.073,
        31.883,
        19.814,
        -18.616,
        -14.836,
        53.964,
        -38.153,
        2.309,
        -5.761,
        -3.334
      ]
    },
    {
      "start": 29.94209,
      "duration": 0.28444,
      "confidence": 1,
      "loudness_start": -22.677,
      "loudness_max_time": 0.02054,
      "loudness_max": -6.203,
      "pitches": [
        0.368,
        0.764,
        0.875,
        1,
        0.514,
        0.272,
        0.224,
        0.065,
        0.124,
        0.119,
        0.187,
        0.338
      ],
      "timbre": [
        49.682,
        106.173,
        -59.255,
        17.24,
        -8.418,
        -24.307,
        -61.567,
        30.532,
        -5.531,
        -11.896,
        -34.967,
        -24.363
      ]
    },
    {
      "start": 30.22653,
      "duration": 0.17406,
      "confidence": 1,
      "loudness_start": -23.535,
      "loudness_max_time": 0.02379,
      "loudness_max": -1.478,
      "pitches": [
        0.193,
        0.225,
        0.082,
        0.138,
        0.213,
        0.266,
        0.599,
        0.492,
        0.205,
        1,
        0.509,
        0.096
      ],
      "timbre": [
        53.665,
        85.166,
        13.27,
        31.357,
        45.225,
        9.18,
        -31.475,
        30.973,
        -6.109,
        22.025,
        19.553,
        16.745
      ]
    },
    {
      "start": 30.40059,
      "duration": 0.09909,
      "confidence": 0.277,
      "loudness_start": -15.676,
      "loudness_max_time": 0.03183,
      "loudness_max": -8.951,
      "pitches": [
        0.234,
        1,
        0.629,
        0.24,
        0.129,
        0.214,
        0.077,
        0.12,
        0.591,
        0.09,
        0.071,
        0.079
      ],
      "timbre": [
        49.32,
        42.805,
        140.904,
        26.765,
        87.744,
        -36.46,
        27.513,
        26.19,
        9.793,
        -1.187,
        4.557,
        6.468
      ]
    },
    {
      "start": 30.49968,
      "duration": 0.16018,
      "confidence": 0.235,
      "loudness_start": -11.479,
      "loudness_max_time": 0.05222,
      "loudness_max": -8.087,
      "pitches": [
        0.387,
        1,
        0.195,
        0.858,
        0.399,
        0.163,
        0.2,
        0.175,
        0.208,
        0.215,
        0.383,
        0.128
      ],
      "timbre": [
        48.537,
        86.316,
        5.443,
        30.112,
        52.413,
        -31.942,
        -8.862,
        30.79,
        -19.383,
        -19.962,
        -28.151,
        -6.51
      ]
    },
    {
      "start": 30.65986,
      "duration": 0.08866,
      "confidence": 0.661,
      "loudness_start": -17.868,
      "loudness_max_time": 0.03941,
      "loudness_max": -9.812,
      "pitches": [
        0.421,
        1,
        0.755,
        0.782,
        0.592,
        0.595,
        0.09,
        0.08,
        0.141,
        0.132,
        0.26,
        0.617
      ],
      "timbre": [
        47.648,
        -34.756,
        5.925,
        -26.182,
        34.829,
        -10.516,
        14.151,
        -5.495,
        13.37,
        26.985,
        10.218,
        -1.129
      ]
    },
    {
      "start": 30.74853,
      "duration": 0.21578,
      "confidence": 0.602,
      "loudness_start": -12.512,
      "loudness_max_time": 0.07073,
      "loudness_max": -4.976,
      "pitches": [
        0.927,
        0.889,
        0.723,
        0.259,
        0.07,
        0.206,
        0.374,
        0.378,
        0.44,
        0.155,
        0.121,
        1
      ],
      "timbre": [
        48.956,
        -19.348,
        15.055,
        12.256,
        26.583,
        -17.253,
        43.547,
        33.021,
        -6.346,
        3.958,
        -47.772,
        23.153
      ]
    },
    {
      "start": 30.96431,
      "duration": 0.28449,
      "confidence": 0.877,
      "loudness_start": -20.375,
      "loudness_max_time": 0.14236,
      "loudness_max": -7.823,
      "pitches": [
        0.106,
        0.089,
        0.068,
        0.082,
        0.062,
        0.11,
        0.121,
        0.426,
        0.741,
        0.562,
        1,
        0.251
      ],
      "timbre": [
        46.049,
        20.397,
        -11.222,
        -13.79,
        41.602,
        30.82,
        -24.433,
        86.154,
        -1.041,
        -29.751,
        -32.714,
        -15.875
      ]
    },
    {
      "start": 31.2488,
      "duration": 0.13297,
      "confidence": 1,
      "loudness_start": -25.152,
      "loudness_max_time": 0.03515,
      "loudness_max": -8.953,
      "pitches": [
        0.271,
        0.122,
        0.095,
        0.135,
        0.16,
        0.045,
        0.074,
        0.072,
        0.963,
        1,
        0.405,
        0.207
      ],
      "timbre": [
        48.752,
        69.707,
        31.556,
        -26.929,
        16.744,
        11.562,
        -59.139,
        0.901,
        -38.758,
        -0.857,
        22.188,
        -46.411
      ]
    },
    {
      "start": 31.38177,
      "duration": 0.16821,
      "confidence": 0.793,
      "loudness_start": -11.36,
      "loudness_max_time": 0.02927,
      "loudness_max": -2.284,
      "pitches": [
        0.335,
        0.315,
        0.14,
        0.336,
        0.22,
        0.334,
        1,
        0.923,
        0.543,
        0.378,
        0.491,
        0.175
      ],
      "timbre": [
        52.14,
        135.638,
        2.899,
        42.682,
        18.764,
        -22.96,
        -56.528,
        51.732,
        13.298,
        -36.411,
        9.604,
        6.058
      ]
    },
    {
      "start": 31.54998,
      "duration": 0.12127,
      "confidence": 0.713,
      "loudness_start": -18.538,
      "loudness_max_time": 0.03138,
      "loudness_max": -7.851,
      "pitches": [
        0.091,
        0.04,
        0.048,
        0.08,
        0.046,
        0.041,
        0.032,
        0.039,
        1,
        0.433,
        0.068,
        0.032
      ],
      "timbre": [
        49.385,
        80.892,
        46.186,
        -2.991,
        18.066,
        -1.343,
        -97.02,
        -23.412,
        -22.535,
        26.987,
        23.134,
        -30.098
      ]
    },
    {
      "start": 31.67125,
      "duration": 0.13397,
      "confidence": 0.432,
      "loudness_start": -11.901,
      "loudness_max_time": 0.02354,
      "loudness_max": -6.2,
      "pitches": [
        0.575,
        0.173,
        0.071,
        0.087,
        0.101,
        0.165,
        0.35,
        0.485,
        0.882,
        0.747,
        1,
        0.32
      ],
      "timbre": [
        48.612,
        73.982,
        -41.733,
        37.207,
        22.377,
        -58.26,
        -30.642,
        2.174,
        -22.887,
        10.018,
        -10.737,
        -10.516
      ]
    },
    {
      "start": 31.80522,
      "duration": 0.13592,
      "confidence": 0.742,
      "loudness_start": -16.968,
      "loudness_max_time": 0.04497,
      "loudness_max": -7.789,
      "pitches": [
        0.602,
        0.641,
        0.149,
        0.073,
        0.153,
        0.289,
        0.553,
        0.395,
        0.845,
        0.82,
        1,
        0.491
      ],
      "timbre": [
        46.84,
        1.388,
        -32.884,
        45.521,
        0.68,
        -11.164,
        -25.86,
        29.995,
        -4.648,
        8.567,
        -30.502,
        -1.117
      ]
    },
    {
      "start": 31.94113,
      "duration": 0.24694,
      "confidence": 0.986,
      "loudness_start": -21.095,
      "loudness_max_time": 0.02325,
      "loudness_max": -5.847,
      "pitches": [
        0.65,
        0.22,
        0.255,
        0.176,
        0.165,
        0.105,
        0.157,
        0.097,
        0.239,
        0.09,
        0.143,
        1
      ],
      "timbre": [
        48.846,
        13.102,
        -33.067,
        52.032,
        15.057,
        -6.873,
        11.522,
        49.329,
        -8.404,
        9.48,
        -24.997,
        -18.481
      ]
    },
    {
      "start": 32.18807,
      "duration": 0.33147,
      "confidence": 1,
      "loudness_start": -22.96,
      "loudness_max_time": 0.07706,
      "loudness_max": -4.674,
      "pitches": [
        0.606,
        0.763,
        0.786,
        0.335,
        0.519,
        0.364,
        1,
        0.241,
        0.088,
        0.115,
        0.349,
        0.716
      ],
      "timbre": [
        44.348,
        101.942,
        -21.645,
        -103.595,
        6.212,
        46.143,
        -16.486,
        21.895,
        6.629,
        -3.232,
        -57.052,
        -10.906
      ]
    },
    {
      "start": 32.51955,
      "duration": 0.30209,
      "confidence": 1,
      "loudness_start": -22.801,
      "loudness_max_time": 0.03588,
      "loudness_max": -3.643,
      "pitches": [
        0.237,
        0.247,
        0.14,
        0.207,
        0.185,
        0.295,
        1,
        0.874,
        0.352,
        0.307,
        0.27,
        0.214
      ],
      "timbre": [
        46.997,
        114.33,
        -7.608,
        82.27,
        27.179,
        21.061,
        -24.868,
        54.5,
        -22.784,
        20.706,
        31.597,
        1.247
      ]
    },
    {
      "start": 32.82163,
      "duration": 0.14494,
      "confidence": 1,
      "loudness_start": -22.26,
      "loudness_max_time": 0.01887,
      "loudness_max": -5.26,
      "pitches": [
        0.528,
        1,
        0.133,
        0.047,
        0.037,
        0.035,
        0.028,
        0.023,
        0.077,
        0.045,
        0.104,
        0.015
      ],
      "timbre": [
        50.098,
        181.567,
        -33.671,
        36.173,
        -13.155,
        -23.314,
        -37.765,
        -3.95,
        10.384,
        23.504,
        -21.121,
        13.651
      ]
    },
    {
      "start": 32.96658,
      "duration": 0.12018,
      "confidence": 0.359,
      "loudness_start": -17.464,
      "loudness_max_time": 0.03074,
      "loudness_max": -10.264,
      "pitches": [
        0.714,
        1,
        0.204,
        0.34,
        0.131,
        0.098,
        0.084,
        0.079,
        0.221,
        0.18,
        0.387,
        0.071
      ],
      "timbre": [
        46.334,
        51.03,
        -50.415,
        -6.019,
        2.401,
        -45.891,
        -42.963,
        20.985,
        -1.133,
        28.388,
        0.684,
        18.405
      ]
    },
    {
      "start": 33.08676,
      "duration": 0.15832,
      "confidence": 0.884,
      "loudness_start": -17.303,
      "loudness_max_time": 0.04297,
      "loudness_max": -6.018,
      "pitches": [
        0.865,
        0.833,
        0.096,
        0.044,
        0.174,
        0.182,
        0.697,
        0.607,
        0.946,
        0.935,
        1,
        0.044
      ],
      "timbre": [
        49.932,
        20.677,
        -32.931,
        -14.004,
        2.985,
        9.312,
        1.598,
        26.778,
        -13.59,
        14.111,
        -0.61,
        -8.428
      ]
    },
    {
      "start": 33.24508,
      "duration": 0.13741,
      "confidence": 0.241,
      "loudness_start": -16.222,
      "loudness_max_time": 0.01149,
      "loudness_max": -10.007,
      "pitches": [
        0.124,
        0.351,
        0.269,
        0.214,
        0.698,
        0.752,
        1,
        0.793,
        0.297,
        0.275,
        0.057,
        0.021
      ],
      "timbre": [
        47.131,
        23.183,
        -32.179,
        22.453,
        -14.442,
        -33.122,
        -19.933,
        20.768,
        -11.407,
        2.091,
        -29.268,
        -0.409
      ]
    },
    {
      "start": 33.38249,
      "duration": 0.27002,
      "confidence": 0.874,
      "loudness_start": -18.664,
      "loudness_max_time": 0.03768,
      "loudness_max": -8.001,
      "pitches": [
        0.129,
        0.568,
        0.146,
        0.089,
        0.123,
        0.197,
        1,
        0.232,
        0.175,
        0.166,
        0.133,
        0.056
      ],
      "timbre": [
        47.698,
        23.377,
        4.914,
        41.398,
        78.204,
        14.998,
        -7.757,
        -34.642,
        -6.34,
        2.765,
        -25.876,
        2.615
      ]
    },
    {
      "start": 33.65252,
      "duration": 0.17905,
      "confidence": 1,
      "loudness_start": -24.848,
      "loudness_max_time": 0.05096,
      "loudness_max": -3.712,
      "pitches": [
        0.35,
        0.299,
        0.146,
        0.272,
        0.293,
        0.314,
        1,
        0.772,
        0.445,
        0.361,
        0.391,
        0.222
      ],
      "timbre": [
        48.28,
        111.213,
        24.297,
        -51.187,
        36.94,
        93.49,
        -33.888,
        51.437,
        -0.278,
        9.756,
        7.941,
        0.344
      ]
    },
    {
      "start": 33.83156,
      "duration": 0.1337,
      "confidence": 0.279,
      "loudness_start": -16.689,
      "loudness_max_time": 0.01842,
      "loudness_max": -8.825,
      "pitches": [
        0.108,
        0.121,
        0.098,
        0.243,
        0.406,
        0.938,
        1,
        0.481,
        0.132,
        0.127,
        0.104,
        0.097
      ],
      "timbre": [
        46.956,
        70.721,
        5.865,
        32.621,
        -1.398,
        -42.043,
        -99.483,
        17.87,
        -20.307,
        2.232,
        1.374,
        -10.373
      ]
    },
    {
      "start": 33.96526,
      "duration": 0.26068,
      "confidence": 0.928,
      "loudness_start": -19.289,
      "loudness_max_time": 0.01984,
      "loudness_max": -6.276,
      "pitches": [
        1,
        0.39,
        0.039,
        0.035,
        0.034,
        0.119,
        0.318,
        0.064,
        0.036,
        0.04,
        0.053,
        0.259
      ],
      "timbre": [
        49.645,
        40.105,
        -29.047,
        47.629,
        17.649,
        -25.328,
        -9.32,
        -19.459,
        -21.587,
        24.188,
        -36.42,
        6.578
      ]
    },
    {
      "start": 34.22594,
      "duration": 0.31968,
      "confidence": 0.99,
      "loudness_start": -21.178,
      "loudness_max_time": 0.03948,
      "loudness_max": -6.765,
      "pitches": [
        0.558,
        1,
        0.432,
        0.156,
        0.162,
        0.12,
        0.357,
        0.094,
        0.107,
        0.076,
        0.087,
        0.292
      ],
      "timbre": [
        47.851,
        27.929,
        -20.881,
        -25.774,
        13.527,
        44.572,
        9.187,
        -39.689,
        -8.071,
        32.913,
        -19.603,
        -14.873
      ]
    },
    {
      "start": 34.54562,
      "duration": 0.28413,
      "confidence": 0.908,
      "loudness_start": -19.527,
      "loudness_max_time": 0.02324,
      "loudness_max": -6.348,
      "pitches": [
        0.458,
        0.66,
        0.924,
        1,
        0.848,
        0.391,
        0.369,
        0.148,
        0.245,
        0.252,
        0.313,
        0.459
      ],
      "timbre": [
        49.633,
        67.326,
        -18.133,
        27.571,
        16.262,
        -27.923,
        -9.234,
        -3.994,
        45.317,
        -19.856,
        -10.759,
        -5.931
      ]
    },
    {
      "start": 34.82975,
      "duration": 0.27873,
      "confidence": 1,
      "loudness_start": -20.065,
      "loudness_max_time": 0.02031,
      "loudness_max": -2.867,
      "pitches": [
        0.371,
        0.522,
        0.44,
        0.606,
        0.428,
        0.698,
        1,
        0.855,
        0.549,
        0.486,
        0.84,
        0.754
      ],
      "timbre": [
        50.885,
        102.362,
        16.735,
        79.706,
        26.013,
        -3.879,
        -29.91,
        50.083,
        11.634,
        -9.647,
        -1.163,
        0.145
      ]
    },
    {
      "start": 35.10848,
      "duration": 0.14522,
      "confidence": 0.975,
      "loudness_start": -21.143,
      "loudness_max_time": 0.02416,
      "loudness_max": -7.349,
      "pitches": [
        0.141,
        1,
        0.214,
        0.523,
        0.31,
        0.144,
        0.142,
        0.136,
        0.134,
        0.153,
        0.169,
        0.061
      ],
      "timbre": [
        49.174,
        81.004,
        10.294,
        12.756,
        4.194,
        -16.02,
        46.168,
        -26.072,
        -28.077,
        19.388,
        3.17,
        -1.559
      ]
    },
    {
      "start": 35.2537,
      "duration": 0.11696,
      "confidence": 0.422,
      "loudness_start": -13.375,
      "loudness_max_time": 0.04025,
      "loudness_max": -8.332,
      "pitches": [
        0.31,
        1,
        0.348,
        0.225,
        0.766,
        0.278,
        0.153,
        0.119,
        0.163,
        0.232,
        0.222,
        0.245
      ],
      "timbre": [
        49.351,
        -14.699,
        2.545,
        0.156,
        35.872,
        -23.116,
        24.381,
        -12.925,
        -7.793,
        -2.799,
        -18.793,
        10.393
      ]
    },
    {
      "start": 35.37066,
      "duration": 0.17433,
      "confidence": 0.596,
      "loudness_start": -13.992,
      "loudness_max_time": 0.0545,
      "loudness_max": -7.266,
      "pitches": [
        1,
        0.802,
        0.091,
        0.154,
        0.233,
        0.248,
        0.571,
        0.594,
        0.829,
        0.792,
        0.982,
        0.101
      ],
      "timbre": [
        49.49,
        -3.838,
        -22.142,
        -29.418,
        14.269,
        -4.546,
        13.589,
        22.505,
        9.198,
        -4.474,
        -25.078,
        -17.32
      ]
    },
    {
      "start": 35.54499,
      "duration": 0.14989,
      "confidence": 0.189,
      "loudness_start": -17.357,
      "loudness_max_time": 0.05782,
      "loudness_max": -11.775,
      "pitches": [
        0.093,
        0.168,
        0.104,
        0.108,
        0.325,
        0.354,
        0.932,
        0.921,
        1,
        0.978,
        0.354,
        0.05
      ],
      "timbre": [
        46.957,
        138.478,
        -84.993,
        -68.427,
        -9.295,
        -44.604,
        -48.785,
        68.747,
        14.425,
        -36.26,
        5.981,
        -10.156
      ]
    },
    {
      "start": 35.69488,
      "duration": 0.16272,
      "confidence": 0.602,
      "loudness_start": -15.346,
      "loudness_max_time": 0.01787,
      "loudness_max": -7.601,
      "pitches": [
        0.146,
        0.689,
        0.114,
        0.162,
        0.317,
        0.276,
        1,
        0.633,
        0.407,
        0.461,
        0.512,
        0.131
      ],
      "timbre": [
        49.485,
        68.838,
        43.873,
        6.152,
        62.088,
        -36.862,
        -31.628,
        -23.336,
        -24.649,
        26.603,
        0.501,
        -14.34
      ]
    },
    {
      "start": 35.8576,
      "duration": 0.10853,
      "confidence": 0.353,
      "loudness_start": -12.413,
      "loudness_max_time": 0.03585,
      "loudness_max": -8.39,
      "pitches": [
        0.074,
        0.233,
        0.198,
        0.081,
        0.14,
        0.284,
        1,
        0.68,
        0.133,
        0.138,
        0.132,
        0.089
      ],
      "timbre": [
        47.894,
        47.092,
        29.228,
        51.312,
        21.525,
        -22.892,
        -38.803,
        -25.771,
        -16.285,
        0.2,
        -14.127,
        8.509
      ]
    },
    {
      "start": 35.96612,
      "duration": 0.28014,
      "confidence": 0.988,
      "loudness_start": -17.098,
      "loudness_max_time": 0.04238,
      "loudness_max": -1.756,
      "pitches": [
        0.245,
        0.243,
        0.171,
        0.403,
        0.403,
        0.392,
        1,
        0.625,
        0.404,
        0.38,
        0.341,
        0.273
      ],
      "timbre": [
        51.889,
        95.525,
        -22.225,
        24.712,
        10.229,
        21.176,
        -51.021,
        40.733,
        18.952,
        -26.723,
        30.094,
        0.131
      ]
    },
    {
      "start": 36.24626,
      "duration": 0.27288,
      "confidence": 0.839,
      "loudness_start": -17.618,
      "loudness_max_time": 0.04246,
      "loudness_max": -5.43,
      "pitches": [
        0.167,
        0.088,
        0.093,
        0.564,
        0.281,
        0.177,
        0.083,
        0.083,
        0.067,
        0.17,
        1,
        0.569
      ],
      "timbre": [
        49.417,
        42.928,
        -35.289,
        14.554,
        35.992,
        13.997,
        -12.232,
        -14.245,
        -19.08,
        42.793,
        -24.736,
        10.879
      ]
    },
    {
      "start": 36.51914,
      "duration": 0.32395,
      "confidence": 0.915,
      "loudness_start": -19.707,
      "loudness_max_time": 0.03671,
      "loudness_max": -6.516,
      "pitches": [
        0.472,
        0.106,
        0.108,
        0.17,
        0.145,
        0.066,
        0.097,
        0.048,
        0.026,
        0.031,
        0.076,
        1
      ],
      "timbre": [
        49.155,
        13.715,
        -1.911,
        -34.295,
        17.324,
        17.289,
        35.864,
        -9.156,
        4.706,
        29.392,
        14.496,
        4.756
      ]
    },
    {
      "start": 36.84308,
      "duration": 0.26236,
      "confidence": 0.625,
      "loudness_start": -12.279,
      "loudness_max_time": 0.01869,
      "loudness_max": -5.519,
      "pitches": [
        0.32,
        0.501,
        1,
        0.826,
        0.394,
        0.152,
        0.169,
        0.077,
        0.103,
        0.128,
        0.289,
        0.493
      ],
      "timbre": [
        48.543,
        73.036,
        -42.141,
        53.68,
        -10.929,
        -43.75,
        -26.216,
        18.386,
        38.963,
        -25.888,
        -28.904,
        -8.027
      ]
    },
    {
      "start": 37.10544,
      "duration": 0.29478,
      "confidence": 1,
      "loudness_start": -24.211,
      "loudness_max_time": 0.03746,
      "loudness_max": -2.366,
      "pitches": [
        0.358,
        0.066,
        0.049,
        0.1,
        1,
        0.462,
        0.258,
        0.156,
        0.198,
        0.13,
        0.078,
        0.744
      ],
      "timbre": [
        49.654,
        54.807,
        -36.972,
        -22.286,
        17.298,
        84.551,
        5.708,
        -7.79,
        -0.139,
        22.665,
        15.693,
        -10.568
      ]
    },
    {
      "start": 37.40023,
      "duration": 0.24989,
      "confidence": 0.199,
      "loudness_start": -13.368,
      "loudness_max_time": 0.05162,
      "loudness_max": -10.259,
      "pitches": [
        0.343,
        0.133,
        0.038,
        0.029,
        0.121,
        1,
        0.38,
        0.033,
        0.027,
        0.133,
        0.048,
        0.05
      ],
      "timbre": [
        47.725,
        18.767,
        -74.927,
        -22.321,
        9.459,
        -33.624,
        0.822,
        -31.945,
        -2.909,
        -8.302,
        -15.298,
        -2.761
      ]
    },
    {
      "start": 37.65011,
      "duration": 0.34313,
      "confidence": 0.906,
      "loudness_start": -15.717,
      "loudness_max_time": 0.20384,
      "loudness_max": -2.213,
      "pitches": [
        0.162,
        0.428,
        0.236,
        0.225,
        0.184,
        0.166,
        1,
        0.182,
        0.094,
        0.186,
        0.262,
        0.189
      ],
      "timbre": [
        53.427,
        50.083,
        -7.958,
        -82.997,
        10.846,
        11.918,
        -8.285,
        19.57,
        -2.923,
        12.821,
        1.028,
        -35.446
      ]
    },
    {
      "start": 37.99324,
      "duration": 0.2912,
      "confidence": 0.332,
      "loudness_start": -8.254,
      "loudness_max_time": 0.11513,
      "loudness_max": -2.267,
      "pitches": [
        0.127,
        0.508,
        0.211,
        0.083,
        0.173,
        0.156,
        1,
        0.276,
        0.108,
        0.108,
        0.174,
        0.167
      ],
      "timbre": [
        56.004,
        30.971,
        13.419,
        -25.859,
        15.302,
        -51.291,
        20.61,
        2.269,
        -14.671,
        6.53,
        -15.17,
        -12.214
      ]
    },
    {
      "start": 38.28444,
      "duration": 0.26086,
      "confidence": 0.261,
      "loudness_start": -5.543,
      "loudness_max_time": 0.00795,
      "loudness_max": -0.627,
      "pitches": [
        0.04,
        0.319,
        0.082,
        0.031,
        0.049,
        0.234,
        1,
        0.252,
        0.066,
        0.048,
        0.127,
        0.055
      ],
      "timbre": [
        53.829,
        59.478,
        -33.334,
        19.466,
        8.878,
        -80.552,
        -14.231,
        6.515,
        -2.332,
        -19.876,
        -12.688,
        4.294
      ]
    },
    {
      "start": 38.54531,
      "duration": 0.19079,
      "confidence": 0.831,
      "loudness_start": -11.881,
      "loudness_max_time": 0.06977,
      "loudness_max": -2.36,
      "pitches": [
        0.117,
        0.418,
        0.203,
        0.155,
        0.131,
        0.341,
        1,
        0.635,
        0.31,
        0.15,
        0.091,
        0.098
      ],
      "timbre": [
        54.851,
        40.181,
        -1.151,
        -35.626,
        26.263,
        6.097,
        -16.544,
        -20.159,
        -27.436,
        12.534,
        -2.855,
        -12.851
      ]
    },
    {
      "start": 38.7361,
      "duration": 0.1059,
      "confidence": 0.379,
      "loudness_start": -6.394,
      "loudness_max_time": 0.02889,
      "loudness_max": -1.762,
      "pitches": [
        0.314,
        0.936,
        0.572,
        1,
        0.948,
        0.458,
        0.525,
        0.576,
        0.41,
        0.387,
        0.51,
        0.305
      ],
      "timbre": [
        55.37,
        34.05,
        5.792,
        15.094,
        -6.085,
        -37.557,
        -25.605,
        8.491,
        -6.876,
        -33.613,
        -13.247,
        8.187
      ]
    },
    {
      "start": 38.842,
      "duration": 0.30218,
      "confidence": 0.183,
      "loudness_start": -8.812,
      "loudness_max_time": 0.01453,
      "loudness_max": -1.418,
      "pitches": [
        0.401,
        0.406,
        0.24,
        0.202,
        0.139,
        0.14,
        0.625,
        0.254,
        0.179,
        0.239,
        0.265,
        1
      ],
      "timbre": [
        55.1,
        38.51,
        -12.283,
        8.428,
        24.747,
        -57.02,
        13.053,
        25.042,
        -13.025,
        20.306,
        -28.76,
        0.059
      ]
    },
    {
      "start": 39.14417,
      "duration": 0.30077,
      "confidence": 0.772,
      "loudness_start": -12.053,
      "loudness_max_time": 0.03476,
      "loudness_max": -3.572,
      "pitches": [
        0.515,
        0.373,
        0.346,
        0.329,
        0.429,
        0.286,
        0.775,
        0.193,
        0.205,
        0.307,
        0.33,
        1
      ],
      "timbre": [
        54.898,
        1.78,
        -0.756,
        -10.086,
        21.585,
        -36.257,
        23.441,
        -14.738,
        -12.097,
        17.414,
        -10.644,
        -5.183
      ]
    },
    {
      "start": 39.44494,
      "duration": 0.25533,
      "confidence": 0.334,
      "loudness_start": -8.157,
      "loudness_max_time": 0.0027,
      "loudness_max": -1.598,
      "pitches": [
        0.475,
        0.127,
        0.167,
        0.264,
        0.211,
        0.091,
        0.305,
        0.154,
        0.153,
        0.185,
        0.131,
        1
      ],
      "timbre": [
        53.11,
        56.017,
        -42.759,
        16.167,
        -0.172,
        -67.715,
        -6.409,
        -20.809,
        -10.695,
        -25.444,
        -22.204,
        7.667
      ]
    },
    {
      "start": 39.70027,
      "duration": 0.13379,
      "confidence": 0.903,
      "loudness_start": -13.788,
      "loudness_max_time": 0.05891,
      "loudness_max": -2.269,
      "pitches": [
        0.728,
        0.294,
        0.173,
        0.17,
        0.163,
        0.628,
        1,
        0.922,
        0.667,
        0.483,
        0.283,
        0.639
      ],
      "timbre": [
        52.295,
        66.489,
        -34.065,
        -35.744,
        19.511,
        33.479,
        -26.409,
        8.619,
        -23.731,
        2.035,
        -29.99,
        -13.533
      ]
    },
    {
      "start": 39.83406,
      "duration": 0.13891,
      "confidence": 0.555,
      "loudness_start": -11.641,
      "loudness_max_time": 0.05912,
      "loudness_max": -4.968,
      "pitches": [
        1,
        0.301,
        0.16,
        0.367,
        0.432,
        0.301,
        0.526,
        0.238,
        0.545,
        0.541,
        0.861,
        0.836
      ],
      "timbre": [
        52.039,
        83.23,
        -40.388,
        -22.569,
        11.762,
        -8.542,
        -19.513,
        -31.166,
        -24.082,
        32.684,
        -25.495,
        4.724
      ]
    },
    {
      "start": 39.97297,
      "duration": 0.3205,
      "confidence": 0.708,
      "loudness_start": -12.075,
      "loudness_max_time": 0.03777,
      "loudness_max": -3.127,
      "pitches": [
        1,
        0.335,
        0.306,
        0.292,
        0.201,
        0.258,
        0.631,
        0.329,
        0.069,
        0.111,
        0.147,
        0.282
      ],
      "timbre": [
        53.802,
        59.292,
        -10.381,
        -39.807,
        -9.786,
        -3.452,
        -21.811,
        -14.38,
        -17.745,
        39.86,
        -10.856,
        -10.168
      ]
    }
  ]
print(len(segments))


segment_durations = []
for i in range(len(segments) - 1):
    segment_durations.append(segments[i+1]["start"] - segments[i]["start"])

avg_segment_duration = np.mean(segment_durations)
print('spotify avg segment duration of always_love_you: ', avg_segment_duration)
'''
