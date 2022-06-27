wget -i "list.txt" --content-disposition -o "wget.log" --no-verbose -b
tail -f wget.log
