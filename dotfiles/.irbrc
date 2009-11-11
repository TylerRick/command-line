#!/bin/env ruby

require 'pp'  # Pretty printer (mostly useful for printing out big objects or hashes, like IRB.conf...)
require 'irb/completion'
require 'fileutils'
require 'date'      # Since irb only gives you ["date/format.rb", "parsedate.rb"] by default!
require 'rubygems'
require 'English'
#require 'extensions/symbol'   # to_proc


IRB.conf[:IRB_RC] = proc do |conf|
	leader = " " * conf.irb_name.length
	conf.prompt_i = "#{conf.irb_name} -> "

  # The prompt for a continuing statement
  conf.prompt_c = leader + '    '

  # The prompt for a continuing string
  conf.prompt_s = leader + '  " '

  conf.return_format = leader + " => %s\n\n"

  puts "Welcome!"
end


# "aliases"/commands
# (Sort of like defining an alias in bash...)
def ri(*names)
  #names.map {|name| name.to_s}
  system("ri " + names[0].to_s)
end
