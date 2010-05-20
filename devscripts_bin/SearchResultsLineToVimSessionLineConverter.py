#!/usr/bin/env python
# Converts cgrep-style "search results lines" into a vim session so that you can quickly open all files in vim that contained your search term.
# Tested by: ~/public/shell/tests/SearchResultsLineToVimSessionLineConverterTest.py
import os, sys, re
from SearchResultsLine import SearchResultsLine

class SearchResultsLineToVimSessionLineConverter:

	def __init__(self, lines):
		self.lines = lines.split("\n")

	def get(self):
		vimLines = ""
		fileNameToVimLine = {}	# {"filename": "badd +1487 filename"}, for example
		lineForFirstFile = None

		for line in self.lines:
			if line != "":
				cgrepLine = SearchResultsLine(line)
				if cgrepLine.parse()["filename"] not in fileNameToVimLine:
					path_prefix = os.getcwd() + '/'
					path_prefix = ''
					escaped_filename = re.sub(" ", '\ ', path_prefix + cgrepLine.parse()["filename"])
					#vimLine = "badd +" + cgrepLine.parse()["line"] + " " + escaped_filename
					vimLine = "tabedit +" + cgrepLine.parse()["line"] + " " + escaped_filename
					vimLines = vimLines + vimLine + "\n"

					fileNameToVimLine.update({cgrepLine.parse()["filename"] : vimLine})
					if lineForFirstFile == None: lineForFirstFile = cgrepLine.parse()["line"]

		if len(fileNameToVimLine) > 0:
			# For some reason buffer 1 is [No File] so let's just jump to buffer 2, shall we?
			#vimLines = vimLines + "b2" + "\n"
			vimLines = vimLines + "tabrewind | bw" + "\n"
			# Jump to the correct line of the first file, because otherwise it sometimes remembers where you were the last time you were in there and ignores the "+line"
			vimLines = vimLines + "execute \":" + str(lineForFirstFile) + "\"" + "\n"

		return vimLines

if __name__ == "__main__":
	lines = ""
	try:
		searchTerm = sys.argv[1]
	except:
		pass
	for line in sys.stdin:
		lines = lines + line
	converter = SearchResultsLineToVimSessionLineConverter(lines)
	output = converter.get()
	print output

	lineCount = output.count("\n")
	if lineCount > 0:
		sys.exit(0)
	else:
		sys.exit(1)
