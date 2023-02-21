EAPX=$1
OUTPUT=$2

for table in $(mdb-tables "$EAPX"); do mdb-json "$EAPX" $table > $OUTPUT/${table}.json ; done
