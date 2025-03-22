#!/bin/bash

# Input CSV file
input_file="input.csv"
# Output CSV file
output_file="output.csv"

# Strings to replace
string_a="64720"
replacement_b="32938"
string_c="29592"
replacement_d="59"

# Use awk to process the file
awk -F',' -v OFS=',' -v a="$string_a" -v b="$replacement_b" -v c="$string_c" -v d="$replacement_d" '
{
    # Replace in the second column
    if ($2 ~ a) gsub(a, b, $2);
    if ($2 ~ c) gsub(c, d, $2);
    print $0;
}' "$input_file" > "$output_file"

echo "Replacement completed. Output saved to $output_file."


