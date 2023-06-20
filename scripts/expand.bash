# Expand a EAP file into a directory of JSON files.
EAPX=$1
OUTPUT=$2

if [ ! -e $EAPX ]; then
    echo "EAPX file not found"
    exit 1
fi

if [ ! -e $OUTPUT ]; then
    echo "Output directory not found"
    exit 1
fi

for table in $(mdb-tables "$EAPX"); do mdb-json "$EAPX" $table > $OUTPUT/${table}.json ; done
