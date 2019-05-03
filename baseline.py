import midi
from os import listdir
from os.path import isfile, join






song = midi.read_midifile("data/Sonata_solo_flute_a_min-fl-1.mid")
track = song[1]
print type(track)
subtrack = track[1]

print track[0:15]