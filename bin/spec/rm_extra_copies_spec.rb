require 'tmpdir'
require 'rubygems'
require 'spec'
require 'facets'
require_local '../rm_extra_copies'

$now = Time.utc(2008,11,12, 7,45,19)

describe Time, "#beginning_of_week" do
  it "should return a Sunday" do
    Time.utc(2008,11,12).beginning_of_week.should == Time.utc(2008,11,9)
  end
end

describe RmExtraCopies::Bucket, "time interval alignment" do

  def sample_quotas
    {
      :minutely => 1,
      :hourly => 3,
      :daily => 1,
      :weekly => '*',
      :monthly => 1,
      :yearly => '*'
    }
  end

  before do
    @command = RmExtraCopies.new('bogus_dir', sample_quotas)
    @now = $now
    @command.stub!(:now).and_return(@now)
  end

  it "should use the time specified by our test" do
    @command.now.should == @now
  end

  it "hour interval should start on the hour, etc." do
    @command.bucket(:minutely).start_time.should == Time.utc(2008,11,12, 7,46,0)
    @command.bucket(:hourly).  start_time.should == Time.utc(2008,11,12, 8,0,0)
    @command.bucket(:daily).   start_time.should == Time.utc(2008,11,13, 0,0,0)
    @command.bucket(:weekly).  start_time.should == Time.utc(2008,11,16, 0,0,0)
    @command.bucket(:monthly). start_time.should == Time.utc(2008,12, 1, 0,0,0)
    @command.bucket(:yearly).  start_time.should == Time.utc(2009, 1, 1, 0,0,0)
  end

end


$command = <<End
rm_extra_copies --force --daily=3 --weekly=3 --monthly=* \
                --now='#{$now.to_s_full}'\
                ../rm_extra_copies_test_dir/db_dumps \
                ../rm_extra_copies_test_dir/maildir
End
describe RmExtraCopies, "when calling `#{$command}`" do
  before do
    Pathname.new("../rm_extra_copies_test_dir/").rmtree rescue nil

    dir='../rm_extra_copies_test_dir/db_dumps/'
    system "mkdir -p #{dir}"
    files = %w[
    db_dump_20080808T0303.sql
    db_dump_20080901T0303.sql
    db_dump_20080910T0303.sql
    db_dump_20081015T0303.sql
    db_dump_20081016T0303.sql
    db_dump_20081017T0303.sql
    db_dump_20081018T0303.sql
    db_dump_20081019T0303.sql
    db_dump_20081020T0303.sql
    db_dump_20081021T0303.sql
    db_dump_20081022T0303.sql
    db_dump_20081023T0303.sql
    db_dump_20081024T0303.sql
    db_dump_20081025T0303.sql
    db_dump_20081026T0303.sql
    db_dump_20081027T0303.sql
    db_dump_20081028T0303.sql
    db_dump_20081029T0303.sql
    db_dump_20081030T0303.sql
    db_dump_20081031T0303.sql
    db_dump_20081101T0303.sql
    db_dump_20081102T0303.sql
    db_dump_20081103T0303.sql
    db_dump_20081104T0303.sql
    db_dump_20081105T0303.sql
    db_dump_20081106T0303.sql
    db_dump_20081107T0303.sql
    db_dump_20081108T0303.sql
    db_dump_20081109T0303.sql
    db_dump_20081110T0303.sql
    db_dump_20081111T0303.sql
    db_dump_20081112T0303.sql
    ]
    files.each do |file|
      system "touch #{dir}/#{file}"
    end

    dir='../rm_extra_copies_test_dir/maildir/'
    system "mkdir -p #{dir}"
    subdirs = %w[
    20081109T0303
    20081110T0303
    20081111T0303
    ]
    subdirs.each do |subdir|
      system "mkdir -p #{dir}/#{subdir}"
      system "touch    #{dir}/#{subdir}/inbox"
      system "touch    #{dir}/#{subdir}/some_other_folder"
    end

    system $command
    # TODO: also capture output of command and check it against expected
  end

  it "keeps/removes the correct files" do
    #p Dir['../rm_extra_copies_test_dir/db_dumps/*'].to_a
    Dir['../rm_extra_copies_test_dir/db_dumps/*'].should == ["../rm_extra_copies_test_dir/db_dumps/db_dump_20081112T0303.sql", "../rm_extra_copies_test_dir/db_dumps/db_dump_20081108T0303.sql", "../rm_extra_copies_test_dir/db_dumps/db_dump_20081031T0303.sql", "../rm_extra_copies_test_dir/db_dumps/db_dump_20081110T0303.sql", "../rm_extra_copies_test_dir/db_dumps/db_dump_20080808T0303.sql", "../rm_extra_copies_test_dir/db_dumps/db_dump_20081101T0303.sql", "../rm_extra_copies_test_dir/db_dumps/db_dump_20080910T0303.sql", "../rm_extra_copies_test_dir/db_dumps/db_dump_20081111T0303.sql"]
  end

  after do
    Pathname.new("../rm_extra_copies_test_dir/").rmtree rescue nil
  end
end

