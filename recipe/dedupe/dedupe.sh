diff "$1" "$2" -rqs | while read line
do
	pattern='^Files (.*) and (.*) are identical$'
	if [[ $line =~ $pattern ]]
	then
		src="${BASH_REMATCH[1]}"
		dest="${BASH_REMATCH[2]}"
		echo Replacing "$dest"
		rm "$dest"
		cp -al "$src" "$dest"
	else
		echo "$line"
	fi
done
