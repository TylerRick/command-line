#!/usr/bin/env ruby
# Deprecated. Use Pathname instead, although I think File would be a better class name...

# This adds some instance methods to File that are strangely missing (they are only available as class methods, which isn't very OOP)
# Note: I don't know where to put this file so that it's usable everywhere we use File objects! Thoughts?

class File
  def dirname
    File.dirname(self.path)
  end

  def basename
    File.basename(self.path)
  end

  def symlink?
    File.symlink?(self.path)
  end
end

