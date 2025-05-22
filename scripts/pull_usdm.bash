# Pull a specified branch for the USDM from the CDISC DDF-RA repository
BRANCH=${1:-main}
INPUTDIR=${2:-input}/$BRANCH

if [ ! -d $INPUTDIR ]; then
    echo "Creating input directory"
    mkdir $INPUTDIR
fi

REMOTE="https://github.com/cdisc-org/DDF-RA/raw/${BRANCH}/Deliverables/UML/USDM_UML.qea"

echo "Pulling USDM from ${REMOTE}"

curl -LJO $REMOTE --output-dir $INPUTDIR 

FILETYPE=$(file $INPUTDIR/USDM_UML.qea | cut -d' ' -f2)

if [ "$FILETYPE" != "SQLite" ]; then
    echo "Branch gone"
    exit 1
fi

# Rename the file to match the branch name
mv $INPUTDIR/USDM_UML.qea $INPUTDIR/${BRANCH}_USDM_UML.qea

REMOTE_CT="https://github.com/cdisc-org/DDF-RA/raw/${BRANCH}/Deliverables/CT/USDM_CT.xlsx"

echo "Pulling USDM CT from ${REMOTE_CT}"

curl -LJO $REMOTE_CT --output-dir $INPUTDIR 

# Rename the CT to match the branch name
mv $INPUTDIR/USDM_CT.xlsx $INPUTDIR/${BRANCH}_USDM_CT.xlsx
