import midi
import os
from os.path import isfile, join
from collections import defaultdict
import random

note_ranges = {
	"violin": (55, 103),
	"viola": (48, 91),
	"cello": (36, 76),
	"contrabass": (28, 67),
	"acoustic guitar (nylon)": (40, 88),
	"tuba": (28, 58),
	"trombone": (40, 72),
	"french horn": (34, 77),
	"trumpet": (55, 82),
	"piccolo": (74, 102),
	"flute": (59, 96),
	"oboe": (58, 91),
	"english horn": (52, 81),
	"clarinet": (50, 94),
	"bassoon": (34, 75),
	"soprano sax": (56, 88),
	"alto sax": (49, 81),
	"tenor sax": (44, 76),
	"baritone sax": (36, 69)
}

def calculateBaseline(tracks):
	print "Calculating baselines..."
	numTracks = 0.
	numCorrect = 0.
	# for each track
	for track in tracks:
		# find its lowest and highest note
		lowest = 127
		highest = 0
		for event in track:
			if type(event) == midi.NoteOnEvent:
				# print "lowest: {} highest: {} event data: {}".format(lowest, highest, event.data[0])
				if event.data[0] < lowest: lowest = event.data[0]
				if event.data[0] > highest: highest = event.data[0]
		# find all the instrument ranges that it fits in
		possible_insts = []
		for inst, ranges in note_ranges.items():
			if ranges[0] <= lowest and ranges[1] >= highest:
				possible_insts.append(inst)
		# pick one randomly
		if len(possible_insts) > 0:
			inst = random.choice(possible_insts)
		else: inst == "other"
		# compare vs. actual and get count
		if inst == getInstrument(track): numCorrect += 1
		numTracks += 1
	print "Guessed {} out of {} tracks correctly".format(numCorrect, numTracks)
	print "{} correct".format(numCorrect/numTracks)


def readTracks():
	print "Reading tracks from file..."
	tracks = []
	data_dir = join(os.getcwd(), "data")
	for file in os.listdir(data_dir):
		if isfile(join(data_dir, file)):
			tracksFromFile(join(data_dir, file), tracks)
		else:
			sub_dir = join(data_dir, file)
			for file in os.listdir(sub_dir):
				tracksFromFile(join(sub_dir, file), tracks)
	print "Done reading."
	return tracks

def getInstrument(track):
	for i in range(len(track)):
		if type(track[i]) == midi.InstrumentNameEvent:
			return track[i].text

def tracksFromFile(filepath, tracks):
	song = midi.read_midifile(filepath)
	tracks.extend(song[1:])

def getInstrumentSet(tracks):
	insts = defaultdict(int)
	for track in tracks:
		inst = getInstrument(track)
		if inst != None: 
			insts[getInstrument(track)] += 1
	return insts

tracks = readTracks()
insts = getInstrumentSet(tracks)
calculateBaseline(tracks)

# song = midi.read_midifile("data/Sonata_solo_flute_a_min-fl-1.mid")
# track = song[1]
# print type(track)
# subtrack = track[1]

# print track[0:15]