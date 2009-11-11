#!/bin/bash
cmd = "svn diff "
echo $cmd
for name in `find ~/svn -name order_options.inc.php`; do
	set cmd = $cmd $name; 
done
echo $cmd

