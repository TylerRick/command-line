#!/usr/bin/env ruby
# http://tfletcher.com/bin/edit_filenames.rb
#
# Batch edit filenames in YourFavouriteTextEditor.
# Call with relative/absolute path, or no arguments for current directory.

Dir.chdir(File.expand_path(ARGV.first || ''))

old_filenames = Dir.glob('*.*').sort

if old_filenames.empty?
  puts 'error: no files to rename'
else
  pipe = IO.popen(ENV['EDITOR'], 'w+')
  pipe.puts old_filenames.join("\n")
  pipe.close_write
  new_filenames = pipe.readlines.collect { |line| line.strip }
  pipe.close
  if new_filenames.size != old_filenames.size
    puts 'error: new file list must be the same size as the original'
  else
    files_renamed = 0
    old_filenames.zip(new_filenames) do |from, to|
      unless from == to
        File.rename(from, to)
        files_renamed += 1
      end
    end
    puts "#{files_renamed} files renamed"
  end
end
