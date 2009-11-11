#!/usr/bin/env python
from CgrepTest import CgrepTest
from TestCase import TestCase
import os, sys
sys.path.append(os.getenv("HOME") + "/svn/tests/common/py/")
from YACP import YACP
config = YACP(os.getenv("HOME") + "/svn/tests/common/conf/common.config")
sys.path.append(config.get("shared_repository_sitepath") + "bin")

class CfgrepTest (CgrepTest):

	def testThatEvenMoreFilesAreExcluded(self):
		expectedOutput = \
self.getBaseDir() + """CgrepTest/a.html:1:needle
"""
		self._CfgrepTest1("needle", "needle", expectedOutput)

	def _CfgrepTest1(self, actualNeedle, searchNeedle, expectedOutput, extraParameters=""):
		os.system("rm -rf CgrepTest")
		os.mkdir("CgrepTest")
		os.system("echo %s > CgrepTest/a.html"% actualNeedle)			# Will list this file
		os.mkdir("CgrepTest/vehicles")
		os.system("echo %s > CgrepTest/vehicles/a"% actualNeedle)
		os.mkdir("CgrepTest/states")
		os.system("echo %s > CgrepTest/states/a"% actualNeedle)
		os.mkdir("CgrepTest/states2")
		os.system("echo %s > CgrepTest/states2/a"% actualNeedle)
		command = "~/svn/devscripts/bin/%s %s %s %s"% (self.getCommand(), searchNeedle, self.myTestDir, extraParameters)
		procHandle = os.popen(command)
		output = procHandle.read()
		os.system("rm -rf CgrepTest")

		self.myAssertEqual(expectedOutput, output)
		
	def getCommand(self):
		return "cfgrep"
	

if __name__ == "__main__":
	TestCase.main()
