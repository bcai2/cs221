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
	# print song[0]
	resolution = song.resolution
	microSecPerBeat = 0.0
	for event in song[0]:
		if type(event) == midi.SetTempoEvent:
			microSecPerBeat = event.get_mpqn()
	secondsPerTick = (microSecPerBeat / resolution) * 1.0 / 1000000
	# print secondsPerTick
	for i in range(1, len(song)):
		song[i] = song[i][:1000]
		song[i].append(secondsPerTick)
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
# less than 40 entries from tracks
# Additionally, caps each instrument at 100 entries (to be implemented).
# This function is not optimized for runtime and could be faster.
def removeSmallAndLargeEntries(tracks, insts):
	print "Removing instrument parts with count < 40..."
	#newTracks = list(tracks)
	for inst in dict(insts):
		if insts[inst] < 40 or inst == 'string ensemble 1':# or not (inst == "trumpet" or inst == "viola"):
			for i in reversed(range(len(tracks))):
				if getInstrument(tracks[i]) == inst or getInstrument(tracks[i]) == None:
					del tracks[i]
			del insts[inst]
	runningInstCounts = {}
	for i in reversed(range(len(tracks))):
		currInst = getInstrument(tracks[i])
		if runningInstCounts.get(currInst, 0) > 99:
			del tracks[i]
		else: runningInstCounts[currInst] = runningInstCounts.get(currInst, 0) + 1
	# insts = runningInstCounts
	print "Done."
	return runningInstCounts

# getTrainingAndTestSets
# Given a set of tracks, splits them by instrument into training and test sets
# Returns training and test sets
# This function is not optimized for runtime and could be faster.
def getTrainingAndTestSet(tracks):
	print "Getting training and test sets..."

	trainingTracks = list(tracks)
	random.seed(1234)
	random.shuffle(trainingTracks)
	testTracks = []
	instCounts = dict(insts)
	removedFromTraining = []
	for inst in instCounts:
		instCounts[inst] = 0

	for i in range(len(tracks)):
		if getInstrument(tracks[i]) not in insts: continue
		if instCounts[getInstrument(tracks[i])] > insts[getInstrument(tracks[i])] * 0.2:
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
# includes regularization of weight vector
def getWeightVector(inst1, inst2, trainTracks, features, eta, gamma, numIters):
	print "Getting weight vector for inst1={} and inst2={}".format(inst1, inst2)
	weights = {}
	for i in range(numIters):
		for j in range(len(trainTracks)):
			oldWeights = dict(weights)
			if getInstrument(trainTracks[j]) == inst1:
				if dotProduct(features[j], weights) < 1.:
					increment(weights, eta, features[j])
					increment(weights, -gamma, oldWeights)
			if getInstrument(trainTracks[j]) == inst2:
				if dotProduct(features[j], weights) * -1 < 1:
					increment(weights, eta * -1, features[j])
					increment(weights, -gamma, oldWeights)
	return weights

# getFeatureVectors
# Given a list of tracks, returns a dict mapping each track to its feature vector
def getFeatureVectors(tracks):
	print "Extracting features..."
	features_list = []
	for i in range(len(tracks)):
		features = defaultdict(lambda:0.0)
		lowest = 127
		highest = 0
		numOnsets = 0
		lengthTotal = 0.0
		noteValueSum = 0
		numNotes = 0
		singleNoteCounter = defaultdict(lambda:0.0)
		bigramCounter = defaultdict(lambda:0.0)
		numBigrams = 0
		trigramCounter = defaultdict(lambda:0.0)
		numTrigrams = 0
		intervalCounter = defaultdict(lambda:0.0)
		numIntervals = 0
		for j in range(len(tracks[i])):
			if type(tracks[i][j]) == midi.NoteOnEvent and tracks[i][j].get_velocity() > 0:
				# feature for average note value
				noteValueSum += tracks[i][j].get_pitch()
				numNotes += 1
				# feature for occurences of each note
				singleNoteCounter[tracks[i][j].get_pitch()] += 1
				# feature for note bigrams
				if j < len(tracks[i]) - 2 and type(tracks[i][j + 2]) == midi.NoteOnEvent and tracks[i][j + 2].get_velocity() > 0:
					featureName = "{} {}".format(tracks[i][j].get_pitch(), tracks[i][j + 2].get_pitch())
					bigramCounter[featureName] += 1
					numBigrams += 1
				# feature for trigrams
				if j < len(tracks[i]) - 4 and type(tracks[i][j + 2]) == midi.NoteOnEvent and type(tracks[i][j + 4]) == midi.NoteOnEvent \
					and tracks[i][j + 2].get_velocity() > 0 and tracks[i][j + 4].get_velocity() > 0:
					featureName = "{} {} {}".format(tracks[i][j].get_pitch(), tracks[i][j + 2].get_pitch(), tracks[i][j + 4].get_pitch())
					trigramCounter[featureName] += 1
					numTrigrams += 1
				# features for lowest and highest notes
				if tracks[i][j].get_pitch() < lowest: 
					features["LOWEST_NOTE"] = tracks[i][j].get_pitch()
					lowest = tracks[i][j].get_pitch()
				if tracks[i][j].get_pitch() > highest: 
					features["HIGHEST_NOTE"] = tracks[i][j].get_pitch()
					highest = tracks[i][j].get_pitch()
				# features for number of occurences of intervals
				if j < len(tracks[i]) - 2 and type(tracks[i][j + 2]) == midi.NoteOnEvent and tracks[i][j + 2].get_velocity() > 0:
					featureName = "INTERVAL {}".format(abs(tracks[i][j].get_pitch() - tracks[i][j + 2].get_pitch()))
					intervalCounter[featureName] += 1
					numIntervals += 1
				#feature for average length between onsets of notes.
				if j < len(tracks[i]) - 2 and type(tracks[i][j + 2]) == midi.NoteOnEvent:
					# print tracks[i][j]
					# print tracks[i][j + 1]
					# print tracks[i][j + 2]
					if (type(tracks[i][j + 1]) == midi.NoteOnEvent and tracks[i][j + 1].get_velocity() == 0) or \
						(type(tracks[i][j + 1]) == midi.NoteOffEvent):
						# print "true"
						numOnsets += 1
						lengthTotal += (tracks[i][j + 1].tick + tracks[i][j + 2].tick)*tracks[i][-1]
		for note in singleNoteCounter:
			singleNoteCounter[note] /= numNotes
			features[str(note)] = singleNoteCounter[note]
		# for bigram in bigramCounter:
		# 	bigramCounter[bigram] /= numBigrams
		# 	features[bigram] = bigramCounter[bigram]
		# for trigram in trigramCounter:
		# 	trigramCounter[trigram] /= numTrigrams
		# 	features[trigram] = trigramCounter[trigram]
		# for inter in intervalCounter:
		# 	intervalCounter[inter] /= numIntervals
		# 	features[inter] = intervalCounter[inter]
		if numOnsets:
			features["DIST_BTWN_NOTES"] = lengthTotal / numOnsets
			numNoteDistFeatures = 3
			for i in range(2, numNoteDistFeatures):
				features["DIST_BTWN_NOTES_" + str(i)] = (lengthTotal / numOnsets)**i
		if numNotes: 
			features["AVG_NOTE_VALUE"] = noteValueSum / numNotes
			numNoteValFeatures = 3
			for i in range(2, numNoteValFeatures):
				features["AVG_NOTE_VALUE_" + str(i)] = (noteValueSum / numNotes)**i
		numHighestLowestNoteFeatures = 3
		for i in range(2, numHighestLowestNoteFeatures):
			features["HIGHEST_NOTE_" + str(i)] = features["HIGHEST_NOTE"]**i
			features["LOWEST_NOTE_" + str(i)] = features["LOWEST_NOTE"]**i
		# print features[i]["DIST_BTWN_NOTES"]
		features_list.append(features)
	print "Done."
	return features_list

# weightVectorsToPickle
# Given a training set, learns weight vectors for pairs of instruments, then stores that set in a pickle file
# takes a while to run
def weightVectorsToPickle(trainTracks):
	weightVectors = {}

	featureVectors = getFeatureVectors(trainTracks)

	for inst1 in insts:
		for inst2 in insts:
			if not inst1 == inst2:
				weightVectors[inst1, inst2] = getWeightVector(inst1, inst2, trainTracks, featureVectors, 0.1, 0.0001, 300) #was 300, 0.001
				#print weightVectors[inst1, inst2]
	wvFile = open("weight_vectors_7", "ab")
	pickle.dump(weightVectors, wvFile)
	wvFile.close()

# pickleToWeightVectors
# Reads a weightVectors dict from a pickle created in weightVectorsToPickle
def pickleToWeightVectors():
	wvFile = open("weight_vectors_7", "rb")
	weightVectors = pickle.load(wvFile)
	return weightVectors

# evaluateOnTestSet
# Given weight vectors and a test set, prints percentage correctly identified and counts
def evaluateOnTestSet(weightVectors, testTracks):
	numEvaluated = 0.
	numCorrect = 0.
	testFeatures = getFeatureVectors(testTracks)
	# print testFeatures[0]
	# print testFeatures[20]
	# print testFeatures[100]
	for i in range(len(testTracks)):
		instGuesses = {}
		for inst1 in insts:
			for inst2 in insts:
				if not inst1 == inst2:
					result = dotProduct(weightVectors[inst1, inst2], testFeatures[i])
					# print "{} {} {}".format(inst1, inst2, result)
					if result > 0:
						instGuesses[inst1] = instGuesses.get(inst1, 0) + 1
					# if result < 0:
					# 	instGuesses[inst1] = instGuesses.get(inst1, 0) - 1 

		maxGuess = 0
		# print instGuesses
		for guess in instGuesses:
			if instGuesses[guess] > maxGuess:
				maxGuess = instGuesses[guess]
		possibilities = []
		for guess in instGuesses:
			if instGuesses[guess] == maxGuess:
				possibilities.append(guess)
		finalGuess = random.choice(possibilities) if len(possibilities) else None
		print "guessed {} for {}. possibilities: {}".format(finalGuess, getInstrument(testTracks[i]), possibilities)
		print instGuesses
		# print max
		numEvaluated += 1
		if finalGuess == getInstrument(testTracks[i]):
			numCorrect += 1
	print "Successfully guessed {} out of {} ({} correct)".format(numCorrect, numEvaluated, numCorrect/numEvaluated)



# ------------------ MAIN ------------------
tracks = readTracks()
insts = getInstrumentSet(tracks)
insts = removeSmallAndLargeEntries(tracks, insts)
print insts 
print len(tracks)
trainTracks, testTracks = getTrainingAndTestSet(tracks)


# uncomment below to relearn weight vectors (e.g., if feature extractor changed)
# weightVectorsToPickle(trainTracks)
weightVectors = pickleToWeightVectors()
print len(weightVectors)
evaluateOnTestSet(weightVectors, testTracks)















