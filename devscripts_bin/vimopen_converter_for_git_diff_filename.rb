#!/usr/bin/env ruby

session_filename= ARGV.shift
# puts ARGV.inspect

File.open(session_filename, 'a') do |session_file|
  ARGV.each do |path|
    path = path.gsub(%r(^a/|^b/), '')
    session_file.puts "badd #{path}"
    session_file.puts "b2"
  end
end

