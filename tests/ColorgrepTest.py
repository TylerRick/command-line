#!/usr/bin/env python
from CfgrepTest import CfgrepTest
import os, sys
sys.path.append(os.getenv("HOME") + "/svn/tests/common/py/")
from TestCase import TestCase
from YACP import YACP
config = YACP(os.getenv("HOME") + "/svn/tests/common/conf/common.config")
sys.path.append(config.get("shared_repository_sitepath") + "bin")

# Tips:
# * colorgrep "new .*Order"
# 		new PromoFaxForOrderReport($this->order
#		(plus everything returned by the following command)
# * colorgrep "new [^\( ]*Order"
#		new PromoFaxForOrderReport($this->order->getID());
#		new HowManyOrdersField($this->sessionInterface);
#		new TestingOrder


# Bugs to expose/fix:
# * None known

class ColorGrepTest (CfgrepTest):
	
	def testThatEvenMoreFilesAreExcluded(self):
		# Have to override this since the one in CfgrepTest would fail
		expectedOutput = \
self.getBaseDir() + """CgrepTest/a.html:1:\033[1;33mNeedle\033[0m
"""
		self._CfgrepTest1("Needle", "Needle", expectedOutput)

	def testCaseInsensitiveSearchTerm(self):
		expectedOutput = \
self.getBaseDir() + """CgrepTest/a.html:1:\033[1;33mNeedle\033[0m
"""% ({"userName": config.get("user_id")})
		# We search for "needle", but still want to see "Needle" in the results since that's how it actually is
		self._CfgrepTest1("Needle", "needle", expectedOutput, extraParameters="i")
		
	def getCommand(self):
		return "colorgrep"
	


if __name__ == "__main__":
	TestCase.main()
