#!/usr/bin/env bash

cat parts.txt | while read p; do
	if [[ "$p" =~ .+\/(.+)\.mu ]]; then
		model=${BASH_REMATCH[1]}
		if [[ $model == 'model' ]]; then
			continue
		fi
		echo "$p -> $model"
		#echo "    <string>$model</string>"
	fi
done

