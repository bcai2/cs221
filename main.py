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
import pickle

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
# helper function for readTracks
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
	print "Done."
	return trainingTracks, testTracks

# getWeightVector
# Given two instruments, a training set, a step size, and number of iterations, 
# returns a weight vector trained to return +1 given a sample of inst1 and -1 given a sample of inst2
def getWeightVector(inst1, inst2, trainTracks, features, eta, numIters):
	print "Getting weight vector for inst1={} and inst2={}".format(inst1, inst2)
	weights = {}
	for i in range(numIters):
		for j in range(len(trainTracks)):
			if getInstrument(trainTracks[i]) == inst1:
				if dotProduct(features[i], weights) < 1.:
					increment(weights, eta, features[i])
			if getInstrument(trainTracks[i]) == inst2:
				if dotProduct(features[i], weights) * -1 < 1:
					increment(weights, eta * -1, features[i])
	return weights

# getFeatureVectors
# Given a list of tracks, returns a dict mapping each track to its feature vector
def getFeatureVectors(tracks):
	print "Extracting features..."
	features = {}
	# feature for number of occurences of each MIDI note
	# additionally, feature for number of occurences of pairs of MIDI notes
	# will be expanded
	for i in range(len(tracks)):
		features[i] = {}
		lowest = 127
		highest = 0
		for j in range(len(tracks[i])):
			if type(tracks[i][j]) == midi.NoteOnEvent:
				if str(tracks[i][j].data[0]) in features:
					features[i][str(tracks[i][j].data[0])] += 1
				else: features[i][str(tracks[i][j].data[0])] = 1
				if j < len(tracks[i]) - 2 and type(tracks[i][j + 2]) == midi.NoteOnEvent:
					featureName = "{} {}".format(tracks[i][j].data[0], tracks[i][j + 2].data[0])
					if featureName in features:
						features[i][featureName] += 1
					else: features[i][featureName] = 1
				# features for lowest and highest notes
				if tracks[i][j].data[0] < lowest: features[i]["LOWEST_NOTE"] = tracks[i][j].data[0]
				if tracks[i][j].data[0] > highest: features[i]["HIGHEST_NOTE"] = tracks[i][j].data[0]
	print "Done."
	return features

# weightVectorsToPickle
# Given a training set, learns weight vectors for pairs of instruments, then stores that set in a pickle file
# takes ~20min to run
def weightVectorsToPickle(trainTracks):
	weightVectors = {}

	featureVectors = getFeatureVectors(trainTracks)

	for inst1 in insts:
		for inst2 in insts:
			if not inst1 == inst2:
				weightVectors[inst1, inst2] = getWeightVector(inst1, inst2, trainTracks, featureVectors, 0.1, 200)

	wvFile = open("weight_vectors_1", "ab")
	pickle.dump(weightVectors, wvFile)
	wvFile.close()

# pickleToWeightVectors
# Reads a weightVectors dict from a pickle created in weightVectorsToPickle
def pickleToWeightVectors():
	wvFile = open("weight_vectors_1", "rb")
	weightVectors = pickle.load(wvFile)
	return weightVectors

# evaluateOnTestSet
# Given weight vectors and a test set, prints percentage correctly identified and counts
def evaluateOnTestSet(weightVectors, testTracks):
	numEvaluated = 0.
	numCorrect = 0.
	testFeatures = getFeatureVectors(testTracks)
	for i in range(len(testTracks)):
		instGuesses = {}
		for inst1 in insts:
			for inst2 in insts:
				if not inst1 == inst2:
					result = dotProduct(weightVectors[inst1, inst2], testFeatures[i])
					if result > 0:
						instGuesses[inst1] = instGuesses.get(inst1, 0) + 1

		max = 0, ""
		# print instGuesses
		for guess in instGuesses:
			if instGuesses[guess] > max[0]:
				max = instGuesses[guess], guess
				print max
				print getInstrument(testTracks[i])
		# print max
		numEvaluated += 1
		if max[1] == getInstrument(testTracks[i]):
			numCorrect += 1
	print "Successfully guessed {} out of {} ({} correct)".format(numCorrect, numEvaluated, numCorrect/numEvaluated)


# ------------------ MAIN ------------------
tracks = readTracks()
insts = getInstrumentSet(tracks)
removeSmallEntries(tracks, insts)
trainTracks, testTracks = getTrainingAndTestSet(tracks)

# uncomment below to relearn weight vectors (e.g., if feature extractor changed)
weightVectorsToPickle(trainTracks)
weightVectors = pickleToWeightVectors()
evaluateOnTestSet(weightVectors, testTracks)















