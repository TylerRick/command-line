#!/usr/bin/env ruby
links = []
data = File.open(ARGV[0]).read
data.scan(%r(url:"(http://[^"]+)")).each do |matches|
  url = matches[0]
  unless url =~ /pagead/
    links << %(<a href="#{url}">#{url}</a>)
  end
end
File.open("#{ARGV[0]}.html", 'w') do |file|
  file.puts \
  %(
  <html>
    <ul>
      #{links.map{|a| "<li>#{a}</li>"}.join("\n")}
    </ul>
  </html>
  )
end


