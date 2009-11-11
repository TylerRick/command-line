#!/usr/bin/ruby
# http://www.paulbetts.org/projects/pathedit-0.1.rb

###########################################################################
#   Copyright (C) 2007 by Paul Betts                                      #
#   paul.betts@gmail.com                                                  #
#                                                                         #
#   This program is free software; you can redistribute it and/or modify  #
#   it under the terms of the GNU General Public License as published by  #
#   the Free Software Foundation; either version 2 of the License, or     #
#   (at your option) any later version.                                   #
#                                                                         #
#   This program is distributed in the hope that it will be useful,       #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#   GNU General Public License for more details.                          #
#                                                                         #
#   You should have received a copy of the GNU General Public License     #
#   along with this program; if not, write to the                         #
#   Free Software Foundation, Inc.,                                       #
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
###########################################################################

require 'rubygems'
require 'pathname'
require 'optparse'
require 'gettext'
require 'tempfile'
require 'logger'
require 'singleton'

include GetText

$logging_level = ($DEBUG ? Logger::DEBUG : Logger::ERROR)

module Platform ; class << self 
	def os
		return :linux if RUBY_PLATFORM =~ /linux/
		return :windows if RUBY_PLATFORM =~ /win/
		return :solaris if RUBY_PLATFORM =~ /solaris/
		return :bsd if RUBY_PLATFORM =~ /bsd/
		return :osx if RUBY_PLATFORM =~ /darwin/
	end
end ; end

def invoke_editor(path)
	editor = ENV['EDITOR']

#	case Platform.os
#	when :osx
#		editor ||= 'open'
#	when :windows
#		editor ||= 'start'
#	end

	unless $stderr.tty?
		raise 'No Terminal!'
	end

	if editor
		# HACK: This is a pretty shady way of resetting stdin to be from
		# a terminal, but Vim does it, and Bram is smarter than me.
		$stdin.reopen($stderr)

		system("#{editor}", path)
		return
	end

	raise 'No Editor!'
end

class PathEdit < Logger::Application
	include Singleton

	def initialize
		super(self.class.to_s) 
		self.level = $logging_level
	end

	def parse(args)
		# Set the defaults here
		results = { :action => :move }

		opts = OptionParser.new do |opts|
			opts.banner = _("Usage: pathedit [options] file1 file2 file3...")
			opts.separator _("If no files are given, the paths will be read from standard input")

			opts.separator ""
			opts.separator _("Specific options:")

			opts.on('-a', _('--action type'), [:copy, :move, :symlink],
				_("Action to perform (one of 'copy', 'move', 'symlink')")) do |x|
				results[:action] = x.to_sym
			end

			opts.separator ""
			opts.separator _("Common options:")

			opts.on_tail("-h", "--help", _("Show this message") ) do
				puts opts
				exit
			end

			opts.on('-d', "--debug", _("Run in debug mode (Extra messages)")) do |x|
				$logging_level = DEBUG
			end

			opts.on('-v', "--verbose", _("Run verbosely")) do |x|
				$logging_level = INFO 
			end

			opts.on_tail("--version", _("Show version") ) do
				puts OptionParser::Version.join('.')
				exit
			end
		end

		opts.parse!(args);	results
	end

	def run
		# Initialize Gettext (root, domain, locale dir, encoding) and set up logging
		bindtextdomain("PathEdit", nil, nil, "UTF-8")
		self.level = Logger::DEBUG

		# Parse arguments
		begin
			results = parse(ARGV)
		rescue OptionParser::MissingArgument
			puts _('Missing parameter; see --help for more info')
			exit
		rescue OptionParser::InvalidOption
			puts _('Invalid option; see --help for more info')
			exit
		end

		# Reset our logging level because option parsing changed it
		self.level = $logging_level
		log DEBUG, 'Starting application'

		# Actually do stuff
		input_paths = (ARGV.length > 0 ? ARGV : nil)
		input_paths ||= STDIN.read.split("\n")

		unless input_paths and input_paths.length > 0
			log ERROR, _('No files specified! Please run --help for more info')
			return
		end

		begin
			temp = Tempfile.new('pathedit')
			temp.puts(input_paths.join("\n")) ; temp.close
			invoke_editor(temp.path)
		rescue Errno
			log ERROR, _("Couldn't create temporary file")
		rescue => e
			log ERROR, _("Couldn't launch editor: " + e)
		end


		output_paths = temp.open.read.split("\n").collect! {|x| x.chomp} ; temp.close!

		if input_paths.length != output_paths.length
			log ERROR, _('Number of paths do not match!')
			return
		end

		(0..input_paths.length-1).each do |i|
			src = input_paths[i] ; dest = output_paths[i]

			next unless src != dest and dest.length > 0

			begin
				pn = Pathname.new(dest).dirname
				pn.mkpath unless pn.exist?

				log INFO, _("Processing ") + pn
				case results[:action]
				when :copy
					if Pathname.new(src).directory?
						FileUtils.cp_r(src, dest)
					else
						FileUtils.cp(src, dest)
					end
				when :move
					FileUtils.mv(src, dest)
				when :symlink
					FileUtils.ln_s(Pathname.new(src).realpath, dest)
				end
			rescue
				log ERROR, _("Couldn't act on ") + src
			end
		end

		log DEBUG, 'Exiting application'
	end
end

$the_app = PathEdit.instance
$the_app.run
