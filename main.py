# main.py
# CS 221 final project by Bryce Cai and Michael Svolos
# This file contains the main code for running the regression algorithm on the dataset.

# This project uses helper functions from util.py from the starter code to CS 221 assignment "sentiment".

import midi
import os
from os.path import isfile, join
from collections import defaultdict
import random
from util import *
import math

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

#get track list
#remove insts with fewer entries



# readTracks
# Returns an array of midi.containers.Track objects, each of which represents an instrumental part
# Reads from currDir/data 
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
	print "Done."
	return tracks

# tracksFromFile
# Given a filepath and an existing array of tracks, reads the midi file from that filepath and 
# adds its tracks to the tracks array
def tracksFromFile(filepath, tracks):
	song = midi.read_midifile(filepath)
	tracks.extend(song[1:])

# getInstrumentSet
# Given an array of tracks, returns a dict that maps each instrument to the number of parts for that 
# instrument
# Returns that dict
def getInstrumentSet(tracks):
	insts = defaultdict(int)
	for track in tracks:
		inst = getInstrument(track)
		if inst != None: 
			insts[getInstrument(track)] += 1
	return insts

# getInstrument
# Given a track, returns the instrument associated with that track by reading the value of 
# midi.InstrumentNameEvent
def getInstrument(track):
	for i in range(len(track)):
		if type(track[i]) == midi.InstrumentNameEvent:
			return track[i].text

# removeSmallEntries
# Given an array of tracks and set of instrument counts, removes all instances of instruments with 
# less than 20 entries from tracks
# This function is not optimized for runtime and could be faster.
def removeSmallEntries(tracks, insts):
	print "Removing instrument parts with count < 20..."
	#newTracks = list(tracks)
	for inst in dict(insts):
		if insts[inst] < 20 or inst == 'string ensemble 1':
			for i in reversed(range(len(tracks))):
				if getInstrument(tracks[i]) == inst or getInstrument(tracks[i]) == None:
					del tracks[i]
			del insts[inst]
	print "Done."
	#return newTracks

# getTrainingAndTestSets
# Given a set of tracks, splits them by instrument into training and test sets
# Returns training and test sets
# This function is not optimized for runtime and could be faster.
def getTrainingAndTestSet(tracks):
	print "Getting training and test sets..."
	trainingTracks = list(tracks)
	testTracks = []
	instCounts = dict(insts)
	removedFromTraining = []
	for inst in instCounts:
		instCounts[inst] = 0

	for i in range(len(tracks)):
		if getInstrument(tracks[i]) not in insts: continue
		if instCounts[getInstrument(tracks[i])] > insts[getInstrument(tracks[i])] * 0.3:
			continue
		track = trainingTracks[i]
		testTracks.append(track)
		removedFromTraining.insert(0, i)
		instCounts[getInstrument(tracks[i])] += 1
	for i in removedFromTraining:
		trainingTracks.pop(i)

	# for inst in insts:
	# 	for i in range(int(math.floor(insts[inst] * 0.3))):
	# 		for i in range(len(tracks)):
	# 			if getInstrument(tracks[i]) == insts[inst]:
	# 				track = trainingTracks.pop(i)
	# 				testTracks.add(track)
	print "Done."
	return trainingTracks, testTracks

# getWeightVector
# Given two instruments, a training set, and a step size, returns a weight vector trained to return +1 given a 
# sample of inst1 and -1 given a sample of inst2
def getWeightVector(inst1, inst2, trainTracks, eta):
	def extractFeatures(track):
		features = {}
		# feature for number of occurences of each MIDI note
		# additionally, feature for number of occurences of pairs of MIDI notes
		for i in range(len(track)):
			if type(track[i]) == midi.NoteOnEvent:
				if str(track[i].data[0]) in features:
					features[str(track[i].data[0])] += 1
				else: features[str(track[i].data[0])] = 1
				if type(track[i + 2]) == midi.NoteOnEvent:
					featureName = "{} {}".format(track[i].data[0], track[i + 2].data[0])
					if featureName in features:
						features[featureName] += 1
					else: features[featureName] = 1

	print "Getting weight vector for inst1={} and inst2={}".format(inst1, inst2)
	weights = {}
	for track in trainTracks:
		if getInstrument(track) == inst1:
			features = extractFeatures(track)
			if dotProduct(features, weights) < 1.:
				increment(weights, eta, features)
		if getInstrument(track) == inst2:
			features = extractFeatures(track)
			if dotProduct(features, weights) * -1 < 1:
				increment(weights, eta * -1, features)

	



tracks = readTracks()
insts = getInstrumentSet(tracks)

removeSmallEntries(tracks, insts)
print insts
print len(tracks)

trainTracks, testTracks = getTrainingAndTestSet(tracks)

print len(trainTracks)
print len(testTracks)
print len(tracks)

weightVectors = {}
for inst1 in insts:
	for inst2 in insts:
		if not inst1 == inst2:
			weightVectors[inst1, inst2] = getWeightVector(inst1, inst2, trainTracks, 0.1)



#split into training and test set
#perform one-to-one reduction of this multiclass classification problem into many binary class. problems
#evaluate on test set















