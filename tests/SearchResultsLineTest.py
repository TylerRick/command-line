#!/usr/bin/env python
import os, sys
sys.path.append(os.getenv("HOME") + "/svn/tests/common/py/")
from TestCase import TestCase
from YACP import YACP
config = YACP(os.getenv("HOME") + "/svn/tests/common/conf/common.config")
sys.path.append(os.getenv("HOME") + "/svn/devscripts/bin/")
from SearchResultsLine import SearchResultsLine

class SearchResultsLineTest (TestCase):

	def testParsing(self):
		cgrepLine = SearchResultsLine("./db/live/tables/order_statuses.sql:6: --:--")
		self.myAssertEqual({
			"filename": "./db/live/tables/order_statuses.sql", 
			"line": "6", 
			"match": " --:--"}, 
			cgrepLine.parse()
		)
	
	def testParsingPlainFilenames(self):
		cgrepLine = SearchResultsLine("./db/live/tables/order_statuses.sql")
		self.myAssertEqual({
			"filename": "./db/live/tables/order_statuses.sql", 
			"line": "1", 
			"match": ""}, 
			cgrepLine.parse()
		)

if __name__ == "__main__":
	TestCase.main()
