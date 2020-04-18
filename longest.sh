cd $1
find ./ -type f \( -name "*.py" -and ! -name "000*" \) -exec wc -l {} + | sed '$d' | sort -n | awk '{print $2";"$1}'
cd - > /dev/null
