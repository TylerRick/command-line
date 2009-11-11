#!/usr/bin/env python
#<a href="http://a1.interclick.com/Interstitial.aspx?adId=0&amp;ind=&amp;wsid=88&amp;requesturl=http%3A//www.dilbert.com/comics/dilbert/archive/images/dilbert2006457980406.gif" target="_new">
#<img src="/comics/dilbert/archive/images/dilbert2006457980406.gif" alt="Today's Comic" border="0" />

import sys
import urllib
sys.path.append("/home/tyler/bin/BeautifulSoup")
from BeautifulSoup import BeautifulSoup

sys.exit()

page = urllib.urlopen("http://www.dilbert.com/")
input = page.read()
soup = BeautifulSoup(input)
foundALogo = False
for img in soup("img"):
	imgStr = str(img)
	if imgStr.find("/comics/dilbert/archive/images") != -1:
		imgStr = imgStr.replace("/comics/dilbert/", "http://www.google.com/comics/dilbert/")
		
		print imgStr
		foundALogo = True
if foundALogo == False:
	print False

