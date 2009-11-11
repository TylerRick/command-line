#!/usr/bin/env python
# Parses a line from cgrep or similar command
# Tested by: ~/svn/devscripts/tests/SearchResultsLineTest.py
import os, sys, re

class SearchResultsLine:

  def __init__(self, line):
    self.line = line

  def parse(self):
    regex = re.compile("([^:]*):([^:]*):?(.*)")
    try:
      return {
        "filename": regex.search(self.line).group(1),
        "line": regex.search(self.line).group(2),
        "match": regex.search(self.line).group(3)
      }
    except AttributeError: # 'NoneType' object has no attribute 'group'
      # If it doesn't appear to be a valid cgrep-results-line, let's assume the whole line is just a plain filename!
      return {
        "filename": self.line,
        "line": "1",
        "match": ""
      }
