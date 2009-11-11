#!/usr/bin/ruby

if ARGV.size < 1
	puts "repeat  --  Repeats a given command (ls / ps / etc.) every second"
	puts "Usage: repeat {CommandToRepeat}"
	exit 1
end

class String
	def is_integer?
		self == self.to_i.to_s
	end
end
class Array
	def pop!
		self.replace self.pop
	end
end

if ARGV[0].is_integer?
	sleep_interval = ARGV[0].to_i
	ARGV.shift
end
sleep_interval ||= 1
puts "Sleep interval: #{sleep_interval}"
puts "Executing: #{ARGV.join(" ")}"

loop do
	system(ARGV.join(" "))
	sleep sleep_interval
end
