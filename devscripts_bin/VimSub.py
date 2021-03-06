#!/usr/bin/env python
# Tested by: ~/svn/devscripts/tests/VimSubTest.py

import os, re, sys, getopt

def printUsage():
	print """Usage: echo "file1 file2 ..." | VimSub.py searchExpression replaceExpression [options]"""
	print """And then, since python can't start vim for you, you have to separately execute:"""
	print """	vim -S ~/tmp/vimsub.vim"""
	sys.exit(1)

def fileWrite(file, contents):
	file = open(file, "w")
	file.write(contents)
	file.close()
		
#def getWhoAmI():
#	getWho = os.popen("whoami")
#	whoami = getWho.readline()[:-1]
#	getWho.close()
#	return whoami
	
# Because not everyone may have a temp dir
tempDir = os.path.expandvars("$HOME") + "/tmp/"
os.system("mkdir -p " + tempDir)

class VimSub:

	files = []
	confirmReplacements = True
	ignoreCase = False

	def __init__(self, files, searchExpression, replaceExpression):
		self.files = files 
		self.searchExpression = searchExpression
		self.replaceExpression = replaceExpression
	
	def getConfirmReplacementsFlag(self):
		if self.confirmReplacements:
			return "c"
		else:
			return ""

	def buildSubstituteCommand(self):
		return "%s/" + self.searchExpression.replace("\\", "\\\\").replace("/", "\\\/") + "/" + \
			self.replaceExpression.replace("\\", "\\\\").replace("/", "\\\/") + "/" + \
			"g" + self.getConfirmReplacementsFlag()

	def getVimFileHeader(self):
		if self.ignoreCase:
			ignoreCaseLine = "set ignorecase"
		else:
			ignoreCaseLine = "set noignorecase"
		return """
source ~/.vimrc
set laststatus=2	" This ensures that the status line is visible (so we can see what file we're editing) even when only one window is open
set nosmartcase
""" + ignoreCaseLine + """
"""
	

	def getVimFileContents(self):
		vimFile = self.getVimFileHeader()

		for file in self.files:
			vimFile = vimFile + """
edit """ + file + """
try
	execute \"""" + self.buildSubstituteCommand().replace('"', r'\"') + """"
catch /^Vim\%((\\a\\+)\)\=:E486/
	echo "Expression not found"
endtry
write
bd
"""
		
		vimFile = vimFile + """
quit
"""

		return vimFile

	def getVimFileName(self):
		return tempDir + "vimsub.vim"

	def writeVimFile(self):
		fileWrite (self.getVimFileName(), self.getVimFileContents())
	

if __name__ == "__main__":

	#---------------------------------------------
	# Handle stdin
	# Files come in on stdin in this format:
	# file1 [file2 [file3 [...]]]
	# [file4 [file5 [file6 [...]]]]
	# [...]
	files = []
	lines = sys.stdin.readlines()
	for line in lines:
		for token in line.split(" "):
			files.append(token.strip())

	if len(files) == 0 or files[0] == '':
		print "VimSub.py: No files were passed in to stdin!"
		sys.exit(1)
	
	print "Files to process: " + " ".join(files)

	#---------------------------------------------
	# Handle arguments
	if len(sys.argv)-1 >= 2:
		# Number of arguments is correct
		pass
	else:
		printUsage()

	searchExpression=sys.argv[1]
	replaceExpression=sys.argv[2]
	options=sys.argv[3:]

	#---------------------------------------------
	# Handle options
	vimsub = VimSub(files, searchExpression, replaceExpression)

	try:
		opts, args = getopt.getopt(options, "fi", ["no-confirm", "ignore-case"])
	except getopt.GetoptError:
		print "VimSub.py: Unrecognized command line argument."
		printUsage()

	for o, a in opts:
		if o in ("-f", "--finish"):
			vimsub.confirmReplacements = False
		if o in ("-i", "--ignore-case"):
			vimsub.ignoreCase = True

	#---------------------------------------------
	#print vimsub.getVimFileContents()
	vimsub.writeVimFile()
	#print vimsub.getVimFileName()

