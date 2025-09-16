#!/bin/bash

# cd "$(dirname "$0")"

file=`mktemp`
cat - > "$file"

./lib/rootca.exp "$file"
rm -f "$file"
