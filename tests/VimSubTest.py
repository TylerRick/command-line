#!/usr/bin/env python
import os, sys
#sys.path.append(os.getenv("HOME") + "/svn/tests/common/py/")
from TestCase import TestCase
#from YACP import YACP
#config = YACP(os.getenv("HOME") + "/svn/tests/common/conf/common.config")
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devscripts_bin'))
from VimSub import VimSub


class VimsubTest (TestCase):

	def testNormalCase(self):
		files = ["a", "b"]
		# create a and b with stuff
		searchExpression = "old"
		replaceExpression = "new"
		vimsub = VimSub(files, searchExpression, replaceExpression)
		
		expectedOutput = vimsub.getVimFileHeader() + r"""
edit a
try
	execute "%s/old/new/gc"
catch /^Vim\%((\a\+)\)\=:E486/
	echo "Expression not found"
endtry
write
bd

edit b
try
	execute "%s/old/new/gc"
catch /^Vim\%((\a\+)\)\=:E486/
	echo "Expression not found"
endtry
write
bd

quit
"""
		
		#self.fileWrite("expected", expectedOutput)
		#self.fileWrite("received", vimsub.getVimFileContents())
		self.myAssertEqual(expectedOutput, vimsub.getVimFileContents())
		self.assertContains(vimsub.getVimFileContents(), "/gc")

	def testEscapingOfParentheses(self):
		files = ["a"]
		searchExpression = r"something \(with a capture group\)"
		replaceExpression = r"something \1"
		vimsub = VimSub(files, searchExpression, replaceExpression)
		
		expectedOutput = vimsub.getVimFileHeader() + r"""
edit a
try
	execute "%s/something \\(with a capture group\\)/something \\1/gc"
catch /^Vim\%((\a\+)\)\=:E486/
	echo "Expression not found"
endtry
write
bd

quit
"""
		
		#self.fileWrite("expected", expectedOutput)
		#self.fileWrite("received", vimsub.getVimFileContents())
		self.myAssertEqual(expectedOutput, vimsub.getVimFileContents())
		self.assertContains(vimsub.getVimFileContents(), "/gc")

	def testEscapingOfQuotes(self):
		# Double-quotes (") must be escaped because the argument for the execute command is delimited by them (").
		files = ["a"]
		searchExpression = r"""$GLOBALS["variableName"] = true;"""
		replaceExpression = r"""$GLOBALS["variableName"] = true;"""
		vimsub = VimSub(files, searchExpression, replaceExpression)
		
		expectedOutput = vimsub.getVimFileHeader() + r"""
edit a
try
	execute "%s/$GLOBALS[\"variableName\"] = true;/$GLOBALS[\"variableName\"] = true;/gc"
catch /^Vim\%((\a\+)\)\=:E486/
	echo "Expression not found"
endtry
write
bd

quit
"""
		self.myAssertEqual(expectedOutput, vimsub.getVimFileContents())
		self.assertContains(vimsub.getVimFileContents(), "/gc")

	def testEscapingDoneBy_buildSubstituteCommand(self):
		files = ["a"]

		searchExpression = r"something \(with a capture group\)"
		replaceExpression = r"something \1"
		vimsub = VimSub(files, searchExpression, replaceExpression)
		self.myAssertEqual(r"%s/something \\(with a capture group\\)/something \\1/gc", vimsub.buildSubstituteCommand())
	
		searchExpression = r"""$GLOBALS["variableName"] = true;"""
		replaceExpression = r"""$GLOBALS["variableName"] = true;"""
		vimsub = VimSub(files, searchExpression, replaceExpression)
		self.myAssertEqual(r"""%s/$GLOBALS["variableName"] = true;/$GLOBALS["variableName"] = true;/gc""", vimsub.buildSubstituteCommand())
	
	def testConfirmReplacementsFlag(self):
		files = ["a", "b"]
		# create a and b with stuff
		searchExpression = "old"
		replaceExpression = "new"
		vimsub = VimSub(files, searchExpression, replaceExpression)
		vimsub.confirmReplacements = False
		self.assertContains(vimsub.getVimFileContents(), "/g")
		self.assertDoesntContain(vimsub.getVimFileContents(), "/gc")
	

	def testBackslashesInSearchExpression(self):
		pass

	def tearDown(self):
		os.system("rm -f expected received");

if __name__ == "__main__":
	TestCase.main()
