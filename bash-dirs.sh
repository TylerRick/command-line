if [[ "" == "$1" ]]; then
	dirs -v
else
	dir=`dirs +$1`
	echo $dir
	#ls $dir
	cd $dir	     # Why does this say 'No such file or directory'?
	#pwd
fi
