#!/usr/bin/env python
#print """<img src=http://www.google.com/logos/stpatricks_06.gif width=290 height=120 border=0 alt="St. Patrick's Day" title="St. Patrick's Day"></a>"""
import sys
import urllib
sys.path.append("/home/tyler/bin/BeautifulSoup")
from BeautifulSoup import BeautifulSoup

page = urllib.urlopen("http://www.google.com")
input = page.read()
soup = BeautifulSoup(input)
foundALogo = False
for img in soup("img"):
	imgStr = str(img)
	if imgStr.find("/logos/") != -1:
		imgStr = imgStr.replace("/logos/", "http://www.google.com/logos/")
		print imgStr
		foundALogo = True
if foundALogo == False:
	print """
		<!--
			<img src="http://www.google.com/images/logo_sm.gif" alt="Go to Google Home" border="0" height="55" vspace="12" width="150" style="float: left; margin:0;">
		-->
		<img src="http://www.google.com/intl/en/images/logo.gif" alt="Go to Google Home" border="0" height="110" vspace="12" width="276" style="float: left; margin:0;">
	"""

