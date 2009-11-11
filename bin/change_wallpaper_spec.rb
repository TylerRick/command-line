#!/usr/bin/ruby

require 'tempfile'
require 'rubygems'
require 'spec'
require 'facets'

load_local 'change_wallpaper' 

describe WallpaperChanger do
  setup do
    config = {
      'dirs' => ['/fake'],
      'log_file' => false,
      'debug' => true
    }

    @object = WallpaperChanger.new(config)
  end

  describe "(requires compiz on your system)" do
    it "gets number of desktops" do
      @object.desktops_count.should >= 1
    end
  end

  describe "with 4 desktops" do
    setup do
      # Unrandomize
      Array.class_eval do
        def pick(n)
          self[0..n-1]
        end
      end
    end

    it "raises an error if no files are found" do
      lambda { @object.start }.should raise_error(RuntimeError)
    end

    it "raises an error if there are fewer files (1) found than desktops (4)" do
      @object.should_receive(:available_files).and_return(%w[a])
      lambda { @object.start }.should raise_error(RuntimeError)
    end

    describe "and 6 available files" do
      setup do
        @object.should_receive(:available_files).and_return(%w[a b c d e f])
      end

      it "picks 4 of them" do
        @object.should_receive(:set_wallpaper).with(%w[a b c d])
        @object.start
      end
    end

  end

end
