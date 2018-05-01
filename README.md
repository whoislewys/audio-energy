# How could this be improved?
Two biggest issues are that comparing the program's loudness and segment calculations to Spotify's, there is too much of a difference.
To see their segment values for a song go [here](https://beta.developer.spotify.com/console/get-audio-analysis-track/) and search for segments at the bottom.
To see their loudness and energy values for a song go [here](https://beta.developer.spotify.com/console/get-audio-features-track/).

Another issue I can think of:
I used *average* segment duration.

[This post](http://runningwithdata.com/post/1321504427/danceability-and-energy) by an Echo Nest engineer
stated that the method they use to dertermine energy includes *loudness* and *segment duration*.

So including segment durations in some other way than getting their mean might improve scores.

# More Info
Read the [paper I wrote](https://docs.google.com/document/d/1kR4edoyA91zsXFrXSqMmjHypDKiKsq-uJGwpeKTT2nA/edit?usp=sharing)
for an overview of the algorithms I used and some more background info on energy and Spotify's other algorithms.
