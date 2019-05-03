import midi
import os
from os.path import isfile, join
from collections import defaultdict

def readTracks():
	tracks = []
	data_dir = join(os.getcwd(), "data")
	for file in os.listdir(data_dir):
		if isfile(join(data_dir, file)):
			tracksFromFile(join(data_dir, file), tracks)
		else:
			sub_dir = join(data_dir, file)
			for file in os.listdir(sub_dir):
				tracksFromFile(join(sub_dir, file), tracks)
	return tracks



def tracksFromFile(filepath, tracks):
	song = midi.read_midifile(filepath)
	tracks.extend(song[1:])

def getInstrumentSet(tracks):
	insts = defaultdict(int)
	for track in tracks:
		for i in range(len(track)):
			if len(track) > i and type(track[i]) == midi.InstrumentNameEvent:
				insts[track[i].text] += 1
	return insts

tracks = readTracks()
insts = getInstrumentSet(tracks)
print insts

# song = midi.read_midifile("data/Sonata_solo_flute_a_min-fl-1.mid")
# track = song[1]
# print type(track)
# subtrack = track[1]

# print track[0:15]