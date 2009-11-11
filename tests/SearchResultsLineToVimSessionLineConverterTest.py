#!/usr/bin/env python
import os, sys
sys.path.append(os.getenv("HOME") + "/svn/tests/common/py/")
from TestCase import TestCase
from YACP import YACP
sys.path.append(os.getenv("HOME") + "/svn/devscripts/bin/")
from SearchResultsLineToVimSessionLineConverter import SearchResultsLineToVimSessionLineConverter

class SearchResultsLineToVimSessionLineConverterTest (TestCase):

	def testWithEmptyInput(self):
		# Let's pretend they did a 'cgrep' search for 'table' and are piping that to our converter...
		converter = SearchResultsLineToVimSessionLineConverter("")
		self.myAssertEqual("", converter.get())

	def testParsing(self):
		# Let's pretend they did a 'cgrep' search for 'table' and are piping that to our converter...
		converter = SearchResultsLineToVimSessionLineConverter( \
"""./db/table.sql:1,000,000: CREATE TABLE table (	-- a comment about my table
./css/screen.css:6.0221415*10^23: table {	/* a comment about my table */
./css/screen.css:the very next line:This line should have *no effect* on the output, because want to put the cursor on the *first* occurence of a search term, not the *last*! ("table!")
A file in the curent working directory:-1:You can't have negative line numbers, silly! But imagine if you could... ("table!")
""")
		self.myAssertEqual(
			\
"""badd +1,000,000 ./db/table.sql
badd +6.0221415*10^23 ./css/screen.css
badd +-1 A file in the curent working directory
b2
execute ":1,000,000"
""",
			converter.get()
		)

	def testParsingFilenamesOnly(self):
		# Let's pretend they did a 'find' search for '.php' and are piping that to our converter...
		converter = SearchResultsLineToVimSessionLineConverter( \
"""
./tests/SomeTest.php
./backend/tests/AnotherTest.php
""")
		self.myAssertEqual(
			\
"""badd +1 ./tests/SomeTest.php
badd +1 ./backend/tests/AnotherTest.php
b2
execute ":1"
""",
			converter.get()
		)

if __name__ == "__main__":
	TestCase.main()
