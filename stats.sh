cd $1
git -c log.showSignature=false log --use-mailmap --no-merges $_since $_until --shortstat \
        --pretty=format:'%H' \
        | grep -E "fil(e|es) changed" --context 1 | grep "\S"
cd - > /dev/null
