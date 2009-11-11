import re
import os
import sys
import inspect
import traceback
import time
import fpformat
import getopt
import urllib
#import ClientCookie
import exceptions
import string
import itertools
from difflib import Differ
from pprint import pformat
#from YACP import YACP
import ftplib
from ftplib import FTP

#class MyCookieJar(ClientCookie.FileCookieJar):
#    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
#		f = open(self.filename, "a")
#		f.write(str(self._cookies))
#		f.close()

#	def cookies(self):
#		return self._cookies

class TestCase:
	"The object from which all python TestCases descend"

	isPass = None
	failureMessage = None
	verbosity = None
	currMethod = None
	assertCount = 0
	preInspectDatabase = False
	postInspectDatabase = False
	largestLineCount = 5
	watchedVariables = {}

	def runAll (self):
		startTime = time.time()

#		self.verifyThatConfigsDontPointToLiveDatabaseOrDie()	

		self.parseCommandLineOptions()
		if self.preInspectDatabase:
			os.system(TestCase.getBaseTestDir() + "common/py/InspectDatabaseTables.py")	

		# Other than passing in a string, I'm not sure how to get the name.
		self.vPrint("\033[1;34m" + inspect.getmodulename(sys.argv[0]) + ".py:\033[1;37m", -1)

		self.setUp()
		self.isPass = {}
		self.failureMessage = {}

		passCount = 0
		failCount = 0

		for method in dir(self):
			if re.search("^test", method) and str(type(getattr(self, method))) == "<type 'instancemethod'>":
				self.currMethod = method
				self.currAssertCount = 0
				self.isPass[method] = []
				self.failureMessage[method] = []

				self.setUpForEachTest()
				self.run(method)
				self.tearDownForEachTest()

				passed = 0
				failed = 0
				outString = ""
				for i in range(0, len(self.isPass[method])):
					if self.isPass[method][i]:
						passed = passed + 1
					else:
						failed = failed + 1

				if failed == 0:
					if self.verbosity == 0:
						self.vPrint(" \033[1;32m[ OK ]\033[0;37m    %s"% (method), 0)
					self.vPrint(" \033[1;32m[ OK ]\033[0;37m    %s \t (%s asserts)"% (method, self.currAssertCount), 1)
					passCount = passCount + 1
				else:
					self.vPrint(" \033[1;31m[ !! ]\033[0;37m    %s"% (method), 0)
					for i in range(0, len(self.isPass[method])):
						if self.verbosity >= 0:
							if self.isPass[method][i]:
								outString = "\t \033[1;32m[ OK ]\033[0;37m    %s"% (method)
							else:
								outString = "\t \033[1;31m[ !! ]\033[0;37m    %s: "% (method)
								#self.failureMessage[method][i] = self.failureMessage[method][i].replace("\\", "\\\\")
								#self.failureMessage[method][i] = self.failureMessage[method][i].replace("\"", "\\\"")
								outString = outString + self.failureMessage[method][i]
							print outString 

					self.vPrint(" \t (%s asserts)"% (self.currAssertCount), 1)
					failCount = failCount + 1

		self.tearDown()
		elapsedTime = time.time() - startTime;
		self.vPrint("    %d PASS, %d FAIL (Elapsed time: %s seconds; %s asserts)"% (passCount, failCount, fpformat.fix(elapsedTime, 3), self.assertCount), -1)
	
		if self.postInspectDatabase:
			os.system(TestCase.getBaseTestDir() + "common/py/InspectDatabaseTables.py")	
		return failCount

	def run (self, testMethodName):
		try:
			self.vPrint("Running %s..."%testMethodName, 4)
			testMethod = getattr(self, testMethodName)
			testMethod()
		except Exception, e:
			if e.__class__ == exceptions.SystemExit:
				sys.exit()
			traceback.print_exc()
			self.failed("Exception raised: " + str(e))

	def myAssert (self, code, expect=True):
		result = eval(code)	
		if result != expect:
			self.failed("%s == %s [%s] -- Parent Function: %s"% (code, expect, result, sys._getframe(1).f_code.co_name))
		else:
			self.passed()

		self.countAssert()

	def myDeny (self, code):
		self.myAssert(code, False)

	def __getComparisons(self, a=None, b=None):
		diffObj = Differ()
		try:
			diffs = list(diffObj.compare(a.splitlines(1), b.splitlines(1)))
			return pformat(diffs)
		except AttributeError, e:
			string = "\nAttributeError: %s\n"%e
			if type(a) == type(None):
				string += " a == None\n"
			if type(b) == type(None):
				string += " b == None\n"

			return string

	def assertEqualStrings(self, v1, v2):
		s1 = s2 = ""
		if v1 == v2:
			self.passed()
		else:
			self.failed(self.__getComparisons(v1, v2))
			
		self.countAssert()

	def myAssertEqual (self, val1, val2):
		if val1 == val2:
			self.passed()
		else:
			self.failed("""Expected: "%s", Received: "%s" """% (val1, val2,))
			
		self.countAssert()

	def myAssertNotEqual(self, val1, val2):
		if val1 != val2:
			self.passed()
		else:
			self.failed("""Expected not to be: "%s", But was: "%s" """% (val1, val2,))
			
		self.countAssert()

	def assertEqualPythonSql(self, pythonValue, sqlValue):
		if str(type(pythonValue)) == "<type 'bool'>":
			self.myAssertEqual(pythonValue, (sqlValue == 1))
		elif str(type(pythonValue)) == "<type 'long'>":
			self.myAssertEqual(pythonValue, sqlValue)
		else:
			self.myAssertEqual(str(pythonValue), str(sqlValue))

	def assertMatches(self, regex, string):
		if re.compile(regex).search(string):
			self.passed()
		else:
			self.failed("""Regex /%s/ not found in string "%s" """%(regex, string))
		

	def passed (self):
		self.isPass[self.currMethod].append(True)
		self.failureMessage[self.currMethod].append("")

	def failed (self, message):
		self.isPass[self.currMethod].append(False)
		message = message + "\n\t           Original assert: " + inspect.stack()[2][4][0].strip()
		if self.watchedVariables.keys().count > 0:
			message += "\n\033[1;35mWatched variables:\n"
			for watchedVar, watchedVal in self.watchedVariables.iteritems():
				message += "\t%s = %s\n"%(watchedVar, watchedVal)
		message += "\033[1;37m"
		#self.printTraceback()
		self.failureMessage[self.currMethod].append(message)

	def addWatchVariable(self, key, val):
		self.watchedVariables[key] = val

	def countAssert (self):
		self.currAssertCount = self.currAssertCount + 1
		self.assertCount = self.assertCount + 1


	def implementMe (self, ):
		"This is just a failing assert that gives a message stating that the test has not been implemented yet."
		self.myAssert("'Test not implemented yet'")

	def assertWebFile (self, url, mimeType):
		"This function asserts that a url returns the expected MIME type"
		fileObject = urllib.urlopen(url)
		self.fileMimeType = fileObject.info().gettype()
		self.expectedMimeType = mimeType
		self.vPrint("Checking for file: \"" + url + "\"", 1)
		self.vPrint("Returned MIME type: \"" + self.fileMimeType + "\"", 2)
		self.vPrint("Expected MIME type: \"" + self.expectedMimeType + "\"", 2)
		fileObject.close()
		self.myAssert("'" + url + "' and self.fileMimeType == self.expectedMimeType")

#	def getClientCookieOpener (self, ):
#		"This function returns a ClientCookie object with an empty CookieJar"
#		# Create a new empty cookie jar
#		newCookieJar = ClientCookie.CookieJar()
#		# Create a new opener object using the empty cookie jar
#		opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(newCookieJar))
#		self.vPrint("Creating a new Cookie Jar", 2)
#		return opener

	def checkSubstring (self, start, end, needle, contents, isIn=True):
		try:
			substring = contents[contents.index(start):contents.index(end, contents.index(start))]
			self.vPrint("Substring: " + substring, 3)
			self.assertContains(substring.strip(), needle, isIn)
		except ValueError:
			if (isIn == True):
				self.failed("Substring wasn't found.")
			else:
				self.passed()
			
	def assertContains (self, haystack, needle, isIn=True):
		if (isIn):
			if haystack != None and needle in haystack:
				self.passed()
			else:
				if haystack != None and haystack.count("\n") > self.largestLineCount:
					self.failed("""Expected "%s" to be in really big buffer, but it wasn't.\nTo see buffer try -vv."""%needle)
				else:
					self.failed("""Expected "%s" to be in "%s", but it wasn't."""%(needle, str(haystack)))
			self.vPrint(haystack, 2)
					
		else :
			if haystack == None or needle not in haystack:
				self.passed()
			else:
				if haystack != None and haystack.count("\n") > self.largestLineCount:
					self.failed("""Expected "%s" to not be in really big buffer, but it was.\nTo see buffer try -vv."""%needle)
				else:
					self.failed("""Expected "%s" to not be in "%s", but it was."""%(needle, str(haystack)))
			self.vPrint(haystack, 2)

	def assertDoesntContain(self, haystack, needle):
		self.assertContains(haystack, needle, False)
	
	def setVerbosity (self, verbosity = 0):
		self.verbosity = int(verbosity)

	def vPrint (self, message, verbosity = 1):
		if self.verbosity >= int(verbosity):
			print message
	
	def fileWrite(self, file, contents):
		file = open(file, "w")
		file.write(contents)
		file.close()

	def fileRead(self, file):
		file = open(file, "r")
		contents = file.read()
		file.close()
		return contents

#	def getCommonConfig(self):
#		return YACP(TestCase.getBaseTestDir() + "common/conf/common.config")
		
	def setUp (self):
		pass

	def tearDown (self):
		pass

	def setUpForEachTest (self):
		pass

	def tearDownForEachTest (self):
		pass

	def parseCommandLineOptions(self):
		if self.verbosity == None:
			self.setVerbosity(0)
		verbCount = 0
		for arg in sys.argv[1:]:
			if arg == "--varbose":
				verbCount = verbCount + 1
			elif arg ==  "--quiet":
				verbCount = verbCount - 1
			elif re.match("^-v+$", arg) != None:
				verbCount = verbCount + (len(arg) - 1)
			elif re.match("^-q+$", arg) != None:
				verbCount = verbCount - (len(arg) - 1)
			elif "I" in arg:
				self.postInspectDatabase = True
			elif "i" in arg:
				self.preInspectDatabase = True
				

			self.setVerbosity(verbCount)
	

	def runningUnitTestsOnly(self):
		return False

	def printTraceback(self):
		for frame in inspect.stack():
			print str(frame[1]) + ":" + str(frame[2]) + ":" + str(frame[3]) + ":" + str(frame[4][0].strip())

	def getAGenericColumnFromGenericTable(self, getColumn="id", tableName="orders", whereColumn="id_name", whereValue=None):
		query = "SELECT %s FROM %s WHERE %s %s;"%(getColumn, tableName, whereColumn, whereValue == None and ' IS NULL' or " = '" + str(whereValue) + "'" )
		result = self.dbConn.db_query(query, "one")
		if result != None:
				return result[0]
		else:
			return None
		
	def stringify(self, delimiter=",", **keyValue):
		conditions = []
		for key, val in keyValue.iteritems():
			if type(val) == type([]):
				conditions.append('''"%s" in (%s)'''%(key, ", ".join(map(lambda v: "$dbv$%s$dbv$"% v, val))))
			else:
				conditions.append('''"%s" %s'''%(key, val == None and 'IS NULL' or "= $dbv$%s$dbv$"% str(val)))
		return delimiter.join(conditions)
		
	def updateAGenericColumnFromGenericTable(self, tableName="orders", whereConditions={}, **columns):
		query = "UPDATE %s SET %s WHERE %s;"%(tableName, self.stringify(**columns), self.stringify(delimiter=" AND ", **whereConditions))
		self.dbConn.db_update(query)
		self.dbConn.commit()

	def getBaseTestDir(className):
		return "/home/" + className.getWhoAmI() + "/svn/tests/"

	def getWhoAmI(className):
		getWho = os.popen("whoami")
		whoami = getWho.readline()[:-1]
		getWho.close()
		return whoami
	
	getBaseTestDir = classmethod(getBaseTestDir)
	getWhoAmI = classmethod(getWhoAmI)

	def connectToFTPServer (self):
		self.ftpServer = FTP()
		self.ftpServer.connect(host=self.config.get("ftp_host"))
		self.ftpServer.login(user=self.config.get("ftp_username"), passwd=self.config.get("ftp_password"))
		try:
			self.ftpServer.mkd(self.config.get("ftp_remote_directory"))
		except ftplib.error_perm:
			pass

#	def verifyThatConfigsDontPointToLiveDatabaseOrDie(self):
#		config = self.getCommonConfig()
#		configFileList = []
#		configFileList.append(config.get("commonBaseTestDir") + "common/conf/common.config")
#		if os.path.isdir(config.get("89glass_repository_path")):
#			configFileList.append(config.get("glassBaseTestDir") + "conf/glass.config")
#			configFileList.append(config.get("glass_bin_dir") + "GlassConfig.py")
#			configFileList.append(config.get("glass_bin_dir") + "GlassConfig.php")
#			configFileList.append(config.get("89glass_frontend_sitepath") + "include/php/config.inc.php")
#			configFileList.append(config.get("89glass_backend_sitepath") + "include/php/pre_company_config.php")
#		if os.path.isdir(config.get("smithsBaseTestDir")):
#			configFileList.append(config.get("smithsBaseTestDir") + "conf/smiths.config")
#			configFileList.append(config.get("smith_includes_sitepath") + "db_config.php")
#			configFileList.append(config.get("qualitysmith_bin") + "QualitySmithConfig.py")
#
#		for configFile in configFileList:
#			if not os.path.isfile(configFile):
#				self.printErrorAboutNotBeingAbleToFindDBConfigFileAndDie(configFile)
#			if self.doesConfigFilePointToLiveDatabase(configFile):
#				self.printHorribleDatabaseErrorMessageAndDie(configFile)
#
#	def doesConfigFilePointToLiveDatabase(self, configFile):
#		file = open(configFile, "r")
#		return ("bb2" in file.read())
#
#	def printErrorAboutNotBeingAbleToFindDBConfigFileAndDie(self, configFile):
#		print "*******************************"
#		print "*******************************"
#		print "WHOA!  **BIG PROBLEM**!"
#		print "*******************************"
#		print "*******************************"
#		print 
#		print "We couldn't find the following config file:"
#		print configFile
#		print "Need to be able to check it and verify that we're not pointed to"
#		print "the live database.  Terminating test!"
#		sys.exit(1)
#
#	def printHorribleDatabaseErrorMessageAndDie(configFile = None):
#		print "*******************************"
#		print "*******************************"
#		print "WHOA!  **BIG PROBLEM**!"
#		print "*******************************"
#		print "*******************************"
#		print 
#		print "At least one config file is pointing to or refers to the LIVE database server, bb2!"
#		print "You probably need to run create_configs.  Terminating test!"
#		if configFile != None:
#			print 
#			print "Config file: " + configFile
#		sys.exit(1)
#	printHorribleDatabaseErrorMessageAndDie = staticmethod(printHorribleDatabaseErrorMessageAndDie)

	def findTestClassesInThisFile(cls):
		testClassesInThisFile = []
		mainModule = __import__("__main__")
		for objName in dir(mainModule):
			obj = getattr(mainModule, objName)
			if str(type(obj)) == "<type 'classobj'>":
				if issubclass(obj, cls) and "__main__" in str(obj):
					testClassesInThisFile.append(obj)

		return testClassesInThisFile
	findTestClassesInThisFile = classmethod(findTestClassesInThisFile)

	def main(cls):
		testClassesInThisFile = cls.findTestClassesInThisFile()
		totalFailures = 0
		for testClass in testClassesInThisFile:
			testObj = testClass()
			totalFailures = totalFailures + testObj.runAll()

		sys.exit(totalFailures)
	main = classmethod(main)
