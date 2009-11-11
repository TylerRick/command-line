#!/usr/bin/env python
import os, sys
sys.path.append(os.getenv("HOME") + "/svn/tests/common/py/")
from TestCase import TestCase
from YACP import YACP
config = YACP(os.getenv("HOME") + "/svn/tests/common/conf/common.config")

class CgrepTest (TestCase):

	myTestDir = "~/svn/devscripts/tests/CgrepTest/"
	

	def testThatFilesAreExcluded(self):
		os.system("rm -rf CgrepTest")
		os.mkdir("CgrepTest")
		os.system("echo needle > CgrepTest/a.html")
		os.system("echo needle > CgrepTest/a.swp")
		os.system("echo needle > CgrepTest/a.tmp")
		os.mkdir("CgrepTest/.svn")
		os.system("echo needle > CgrepTest/.svn/a")
		procHandle = os.popen("~/svn/devscripts/bin/cgrep needle " + self.myTestDir)
		output = procHandle.read()
		os.system("rm -rf CgrepTest")

		expectedOutput = \
self.getBaseDir() + """CgrepTest/a.html:1:needle
"""% ({"userName": config.get("user_id")})
		self.myAssertEqual(expectedOutput, output)

	def testDollarSigns(self):
		# This was added to expose a bug
		os.system("rm -rf CgrepTest")
		os.mkdir("CgrepTest")
		os.system("""echo "\$CONFIG" > CgrepTest/a.php""")
		procHandle = os.popen("""~/svn/devscripts/bin/cgrep "\$CONFIG" """ + self.myTestDir)
		output = procHandle.read()
		os.system("rm -rf CgrepTest")

		expectedOutput = \
self.getBaseDir() + """CgrepTest/a.php:1:$CONFIG
"""
		self.myAssertEqual(expectedOutput, output)

	def testHyphen(self):
		# This was added to expose a bug
		os.system("rm -rf CgrepTest")
		os.mkdir("CgrepTest")
		os.system("""echo "command -complete=something" > CgrepTest/a.vim""")

		# You have to escape the - !
		procHandle = os.popen("""~/svn/devscripts/bin/cgrep "\-complete=something" """ + self.myTestDir + """ 2>&1""")

		output = procHandle.read()
		os.system("rm -rf CgrepTest")

		expectedOutput = \
self.getBaseDir() + """CgrepTest/a.vim:1:command -complete=something
"""
		self.myAssertEqual(expectedOutput, output)
		self.assertDoesntContain(output, "grep: invalid max count")

	def getBaseDir(self):
		return """/home/%(userName)s/svn/devscripts/tests/"""% ({"userName": config.get("user_id")})
		
	

if __name__ == "__main__":
	TestCase.main()
