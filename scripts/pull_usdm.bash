BRANCH=${1:-main}
INPUTDIR=${2:-input}

if [! -d $INPUTDIR ]; then
    echo "Creating input directory"
    mkdir $INPUTDIR
fi

REMOTE="https://github.com/cdisc-org/DDF-RA/raw/${BRANCH}/Deliverables/UML/USDM_UML.eapx"

echo "Pulling USDM from ${REMOTE}"

curl -LJO $REMOTE --output-dir $INPUTDIR 

# Rename the file to match the branch name
mv $INPUTDIR/USDM_UML.eapx $INPUTDIR/${BRANCH}_USDM_UML.eapx
