cd $1
git -c log.showSignature=false log --use-mailmap --no-merges $_since $_until \
        --pretty=format:'{ ^^%^%^XDcommit^^%^%^XD: ^^%^%^XD%H^^%^%^XD, ^^%^%^XDsanitized_subject_line^^%^%^XD: ^^%^%^XD%f^^%^%^XD, ^^%^%^XDauthor^^%^%^XD: {    ^^%^%^XDname^^%^%^XD: ^^%^%^XD%aN^^%^%^XD,    ^^%^%^XDemail^^%^%^XD: ^^%^%^XD%aE^^%^%^XD,    ^^%^%^XDdate^^%^%^XD: ^^%^%^XD%aI^^%^%^XD  },  ^^%^%^XDcommiter^^%^%^XD: {    ^^%^%^XDname^^%^%^XD: ^^%^%^XD%cN^^%^%^XD,    ^^%^%^XDemail^^%^%^XD: ^^%^%^XD%cE^^%^%^XD,    ^^%^%^XDdate^^%^%^XD: ^^%^%^XD%cI^^%^%^XD  }},' \
        | sed "$ s/,$//" \
        | sed ':a;N;$!ba;s/\r\n\([^{]\)/\\n\1/g' \
        | sed ':a;N;$!ba;s/\n\r\([^{]\)/\\n\1/g' \
        | sed ':a;N;$!ba;s/\n\n\([^{]\)/\\n\1/g' \
        | sed ':a;N;$!ba;s/\t\([^{]\)/\\t\1/g' \
        | sed ':a;N;$!ba;s/\n\([^{]\)/\\n\1/g' \
        | sed ':a;N;$!ba;s/\r\([^{]\)/\\n\1/g' \
        | awk 'BEGIN { print("[") } { print($0) } END { print("]") }' \
        | sed 's/"/\\"/g' | sed 's/\^^%^%^XD/"/g'
cd - > /dev/null