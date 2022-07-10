git status . -uall --short | grep ?? | while read -r raw_line
do
	fname=${raw_line##?? }
	printf "Checking ${fname}..."
	ccc=($(cksum -o3 "${fname}"))
	ccc=$(printf "%X" ${ccc[0]})
	if [[ $fname =~ $ccc ]]
	then echo ok
	else echo failed with crc ${ccc}!! && break
	fi
done
