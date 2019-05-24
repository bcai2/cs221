# main.py
# CS 221 final project by Bryce Cai and Michael Svolos
# This file contains the main code for running the regression algorithm on the dataset.

#get track list
#remove insts with fewer entries
#split into training and test set
#perform one-to-one reduction of this multiclass classification problem into many binary class. problems
#evaluate on test set


# readTracks
# Returns an array of 
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

def tracksFromFile(filepath, tracks):
	song = midi.read_midifile(filepath)
	tracks.extend(song[1:])

tracks = readTracks()
print type(tracks[0])