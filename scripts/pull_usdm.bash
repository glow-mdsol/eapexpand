#!/bin/bash
BRANCH=${1:-main}

REMOTE="https://github.com/cdisc-org/DDF-RA/raw/${BRANCH}/Deliverables/UML/USDM_UML.eapx"

echo "Pulling USDM from ${REMOTE}"

curl -LJO $REMOTE --output-dir input 

# Rename the file to match the branch name
mv input/USDM_UML.eapx input/${BRANCH}_USDM_UML.eapx
