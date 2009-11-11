# Copyright 2008 Tyler Rick
# License: GPL

# Tested by: spec/rm_extra_copies_spec.rb

require 'fileutils'
require 'pathname'
require 'delegate'

require 'rubygems'
require 'facets/time'
require 'colored'
require 'quality_extensions/module/attribute_accessors'

# Until facets gets patched proper, we'll monkey patch it here:
#require '/home/tyler/dev/ruby/facets/lib/core/facets/time/hence'
class Time

  if defined?(::ActiveSupport)

    alias_method :in, :since
    alias_method :hence, :since

  else

    # Returns a new Time representing the time
    # a number of time-units ago.
    #
    def ago(number, units=:seconds)
      time =(
        case units.to_s.downcase.to_sym
        when :years
          set(:year => (year - number))
        when :months
          y = ((month - number) / 12).to_i
          #puts "(#{month} - #{number}) / 12 == #{y}"

          new_month = ((month - number - 1) % 12) + 1
          y += 1 if new_month > month
          #puts y

          set(:year => (year - y), :month => new_month)
        when :weeks
          self - (number * 604800)
        when :days
          self - (number * 86400)
        when :hours
          self - (number * 3600)
        when :minutes
          self - (number * 60)
        when :seconds, nil
          self - number
        else
          raise ArgumentError, "unrecognized time units -- #{units}"
        end
      )
      dst_adjustment(time)
    end
    #
    # Returns a new Time representing the time
    # a number of time-units hence.

    def hence(number, units=:seconds)
      time =(
        case units.to_s.downcase.to_sym
        when :years
          set( :year=>(year + number) )
        when :months
          y = ((month + number - 1) / 12).to_i
          m = ((month + number - 1) % 12) + 1
          set(:year => (year + y), :month => m)
        when :weeks
          self + (number * 604800)
        when :days
          self + (number * 86400)
        when :hours
          self + (number * 3600)
        when :minutes
          self + (number * 60)
        when :seconds
          self + number
        else
          raise ArgumentError, "unrecognized time units -- #{units}"
        end
      )
      dst_adjustment(time)
    end

    alias_method :in, :hence
    alias_method :since, :hence

    # Adjust DST
    #
    # TODO: Can't seem to get this to pass ActiveSupport tests.
    # Even though it is essentially identical to the
    # ActiveSupport code (see Time#since in time/calculations.rb).
    # It handles all but 4 tests.
    def dst_adjustment(time)
      self_dst = self.dst? ? 1 : 0
      time_dst = time.dst? ? 1 : 0
      seconds  = (self - time).abs
      if (seconds >= 86400 && self_dst != time_dst)
        time + ((self_dst - time_dst) * 60 * 60)
      else
        time
      end
    end

  end

end


class DateTime
  def to_time
    Time.mktime(year, month, day, hour, min, sec)
  end
end

class Time
  def to_s
    #strftime("%Y%m%dT%H%M%S")
    strftime("%Y-%m-%d %H:%M")
  end
  def to_s_full
    strftime("%Y-%m-%d %H:%M:%S")
  end

  # /usr/lib/ruby/gems/1.8/gems/activesupport-2.1.2/lib/active_support/core_ext/time/calculations.rb

    def beginning_of_day
      change(:hour => 0)
    end
    alias :midnight :beginning_of_day

    # Returns a new Time representing the "start" of this week (Sunday, 0:00)
    def beginning_of_week
      days_to_sunday = self.wday
      self.ago(days_to_sunday, :days).midnight
    end
    alias :sunday :beginning_of_week

end

# AKA PruneBackups, SparsenDir
class RmExtraCopies
  #---------------------------------------------------------------------------------------------------------------------------------------------------

  @@allowed_bucket_names = [:minutely, :hourly, :daily, :weekly, :monthly, :yearly]
  mattr_reader :allowed_bucket_names

  #---------------------------------------------------------------------------------------------------------------------------------------------------
  # Options
  @@options = [:get_time_from, :ignore_files ,:verbosity, :time_format, :now, :force, :no_color]
  mattr_reader :options
  mattr_accessor *@@options

  @@get_time_from = :filename
  def self.get_time_from=(new)
    @@get_time_from = new.to_sym
    raise "Unknown value for #{RmExtraCopies.get_time_from}" unless @@get_time_from.in?([:filename, :file_system])
  end

  @@ignore_files = nil
  @@verbosity = 1
  @@force = false
  @@color = true

  @@now = Time.now
  def self.now=(new)
    time = DateTime.strptime('2008-11-12 07:45:00', '%Y-%m-%d %H:%M:%S').to_time
    @@now = new
    puts "Using alternate now: #{@@now}"
  end

  @@time_format = /(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})?/
  @@time_format_parts = [:Y,:m,:d, :H,:M,:S]
  # TODO: Maybe use something like this for interpreting time, rather than a regexp? DateTime.strptime("27/Nov/2007:15:01:43 -0800", "%d/%b/%Y:%H:%M:%S %z")
  def self.time_format=(new)
    # TODO: accept format strings such as 'H:M:S d.m.Y.' and 'Y-m-d H:M:S'
    # TODO: do error checking
  end


  #---------------------------------------------------------------------------------------------------------------------------------------------------

  class Bucket
    attr_reader :parent, :name, :quota, :keepers
    @@quota_format = %r[(\d+|\*)(/\d+)?]

    def initialize(parent, name, quota)
      @parent = parent
      @name = name
      (
      raise "Invalid quota '#{quota}'" unless quota.is_a?(Fixnum) || quota =~ @@quota_format
      @quota = quota
      )
      @keepers = []
    end

    def unit
      {
        :minutely => :minutes,
        :hourly   => :hours,
        :daily    => :days,
        :weekly   => :weeks,
        :monthly  => :months,
        :yearly   => :years,
      }[@name.to_sym]
    end

    def start_time
      start_time = parent.now.dup
      if parent.align_at_beginning_of_time_interval
        beginning_of_interval = 
          case unit
          when :minutes
            start_time.change(:sec => 0)
          when :hours
            start_time.change(:min => 0)
          when :days
            start_time.change(:hour => 0)
          when :weeks
            start_time.beginning_of_week
          when :months
            start_time.change(             :day => 1, :hour => 0)
          when :years
            start_time.change(:month => 1, :day => 1, :hour => 0)
          else
            raise "unexpected unit #{unit}"
          end
        # We actually want to use the *next* interval (in the future) as our start_time because we will be using this as our max and going backwards in time...
        beginning_of_interval.hence(1, unit)
      else
        start_time
      end
    end

    def keep(keeper)
      @keepers << keeper
    end

    def still_need
      if keep_all?
        1 # it has insatiable hunger for keepers that can never be satisfied ... always just 1 more ...
      else
        @quota - @keepers.size
      end
    end

    def keep_all?; quota =~ /\*/ end
    
    def satisfied?
      if keep_all?
        false # it has insatiable hunger for keepers that can never be satisfied
      else
        still_need == 0
      end
    end
  end

  class File < DelegateClass(::Pathname)
    attr_reader :filename, :file

    def initialize(filename)
      super(Pathname.new(filename))
    end

    def full_path
      dirname.to_s + '/' + filename
    end

    def filename
      basename.to_s
    end
    def to_s
      filename
    end

    def time
      if RmExtraCopies.get_time_from == :filename
        if filename =~ RmExtraCopies.time_format
          y,m,d, h,i,s = $1,$2,$3, $4,$5,$6
          Time.mktime(y,m,d, h,i,s)
        else
          nil
        end
      elsif RmExtraCopies.get_time_from == :file_system
        file.mtime
      else
        raise "Unknown value for #{RmExtraCopies.get_time_from}"
      end
    end

    def has_time?; !!time end
    def ignored?
      !has_time? or
      RmExtraCopies.ignore_files && filename =~ RmExtraCopies.ignore_files
    end
  end

  attr_reader :align_at_beginning_of_time_interval, :files_with_times
  attr_accessor :dir

  def initialize(dir, quotas)
    @align_at_beginning_of_time_interval = true
    @dir = dir
    @buckets = {}
    @@allowed_bucket_names.each do |name|
      quota = quotas[name]
      @buckets[name] = Bucket.new(self, name, quota) unless quota.nil?
    end

    puts "Processing #{@dir}/*".magenta
    files = Dir["#{@dir}/*"].map { |filename|
      file = File.new(filename)
    }
    @files_with_times = files.
      reject {|file| !file.has_time?}.
      sort { |a, b|
             a.time <=> b.time
           }.
      reverse

  end

  def bucket_remaining(bucket_name, decr = nil)
    send("#{bucket_name}=", send("#{bucket_name}") - decr) if decr
    send "#{bucket_name}"
  end

  def buckets
    @buckets.values
  end
  def bucket(name)
    @buckets[name] or raise "unknown bucket '#{name}'"
  end

  def now
    Time.now
  end

  def delete_non_keepers
    #raise "Didn't find any files to keep?!" unless keepers.any?
    files_with_times.each do |file|
      if (buckets = buckets_with_file(file)).any?
        puts "#{file.full_path}: in buckets: #{buckets.map(&:name).join(', ')}".green
      else
        puts "#{file.full_path}: delete".red
      end
    end

    if @@force == false
      print "Continue with deletions? (yes or no) >".magenta
      response = STDIN.gets
      (puts "Aborting"; return) unless response.chomp.downcase == 'yes'
    end

    files_with_times.each do |file|
      if (buckets = buckets_with_file(file)).any?
        #
      else
        file.unlink
      end
    end
  end

  def buckets_with_file(file)
    buckets.find_all {|bucket| bucket.keepers.include?(file)}
  end

  def delete(files)
    puts "Deleting files: #{files.join(', ')}..."
  end

  def earliest_file_time
    files_with_times.last.time
  end

  def run
    raise "Must keep at least 1 file from at least one time bucket" if buckets.empty?
    (puts "Found no files with times! Aborting."; return) if files_with_times.empty?

    # Fill each bucket until its quota is met
    buckets.each do |bucket|
      puts "Trying to fill bucket '#{bucket.name}' (quota: #{bucket.quota})...".magenta

      time_max = bucket.start_time
      time_min = time_max.ago(1, bucket.unit)

      #puts "Earliest_file_time: #{earliest_file_time}"
      while time_max > earliest_file_time
        print "Checking range (#{time_min} .. #{time_max})... ".yellow if verbosity >= 1
        new_keeper = files_with_times.detect {|file|
          #print "#{file}? "
          time_min <= file.time &&
                      file.time < time_max
        }
        if new_keeper
          puts "found keeper #{new_keeper}".green if verbosity >= 1
          bucket.keep new_keeper
        else
          #puts "found no keepers".red if verbosity >= 1
          puts "" if verbosity >= 1
        end

        time_max = time_min
        #puts "Stepping back from #{time_min} by 1 #{bucket.unit} => #{time_min.ago(1, bucket.unit)}"
        time_min = time_min.ago(1, bucket.unit)
        (puts 'Filled quota!'.green; break) if bucket.satisfied?
      end
    end

    delete_non_keepers
  end
end
