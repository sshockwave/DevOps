rm -f list.txt output.mp4
for i in *.mp4
do
	echo file \'$i\' >> list.txt
done
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4
rm list.txt
