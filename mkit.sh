FMT="cpt"

#  LOCAL resources
#  Convert ttl to cpt for AMI.py GPT prompt ingest:
python3 ttldump.py --format $FMT ami.ttl  > ami.$FMT
python3 ttldump.py --format $FMT exc.ttl  > local.$FMT
python3 ttldump.py --format $FMT exr.ttl  >> local.$FMT

#  This is the LOCAL AMI triplestore:
python3 ttlldr.py --drop --coll ami5 ami.ttl data.ttl exc.ttl exr.ttl


#  This simulates a remote triplestore.  We do this by running
#  another jenaserver on a different port that points to
#  a different collection in the "semantic" database.
python3 ttldump.py --format $FMT xts.ttl  > xts.$FMT
python3 ttlldr.py --drop --coll amiX xts.ttl

