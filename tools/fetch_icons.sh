#!/bin/bash

rm -f "items.csv"
curl "http://minecraft-ids.grahamedgecombe.com/images/sprites/items-3.png" > items.png
curl -s "http://minecraft-ids.grahamedgecombe.com/" | grep "items/" | while read line ; do
	id="`echo "$line" | sed -e 's/.*items\/\(.*\)".*/\1/'`"
	name="`echo "$line" | sed -e 's/.*">\(.*\)<\/a>.*/\1/'`"
	echo "$id;$name" >> items.csv
done
