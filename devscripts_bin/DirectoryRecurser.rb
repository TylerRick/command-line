#!/usr/bin/env ruby
# Tested by: /bin/false

class DirectoryRecurser
  def initialize(exclude_files = [])
    @exclude_files = exclude_files
    @exclude_files += [".", ".."]  # We *always* want to exclude these or we could get stuck in infinite loops!
  end

  def recurse(dir_name, &callback)
    Dir.foreach(dir_name) do |file_name|
      if !@exclude_files.include?(file_name)
        $stdout.flush

        full_path = File.join(dir_name, file_name)
        begin
          callback.call(full_path)

          # Recurse
          if File.directory?(full_path) && !File.symlink?(full_path)
            recurse(full_path, &callback)
          end
        rescue Errno::ENOENT  # "File does not exist" error
          p $!
        end
      end
    end
  end
end


# Example usage:
#  recurser = DirectoryRecurser.new([".svn"])
#  recurser.recurse(start_dir) { |file_path| 
#    file = File.new(file_path)
#    puts file.path
#  }

