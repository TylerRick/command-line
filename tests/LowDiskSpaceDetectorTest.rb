#!/bin/env ruby

require 'test/unit'
require File.join('..', 'bin', 'LowDiskSpaceDetector')
require 'pp'

class Array
  def loose_include?(sought)
    for element in self
      #puts "Is '#{sought}' in '#{element}'?"
      return element.include?(sought)
    end
  end
end

class MockLowDiskSpaceDetector < LowDiskSpaceDetector
  def df
    return "
Filesystem           1K-blocks      Used Available Use% Mounted on
/dev/sda0               101086     22572     73295 100% /var
/dev/sda1               101086     22572     73295  99% /home
/dev/sdb1               101086     22572     73295  92% /boot
/dev/shm               1035184         0   1035184   0% /dev/shm
"
  end
end

class ThisTest < Test::Unit::TestCase
  def test_90_percent
    expected_partitions = [
      "/dev/sda0               101086     22572     73295 100% /var",
      "/dev/sda1               101086     22572     73295  99% /home",
      "/dev/sdb1               101086     22572     73295  92% /boot"
    ]
    partitions = MockLowDiskSpaceDetector.new(90).get_low_partitions
    assert_equal expected_partitions, partitions
  end

  def test_99_percent
    expected_partitions = [
      "/dev/sda0               101086     22572     73295 100% /var",
      "/dev/sda1               101086     22572     73295  99% /home"
    ]
    partitions = MockLowDiskSpaceDetector.new(99).get_low_partitions
    assert_equal expected_partitions, partitions
  end
end

