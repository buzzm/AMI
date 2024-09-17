FMT="cpt"
python3 ttldump.py --format $FMT ami.ttl  > ami.$FMT
python3 ttldump.py --format $FMT exc.ttl  > local.$FMT
python3 ttldump.py --format $FMT exr.ttl  >> local.$FMT

python3 ttlldr.py --drop *.ttl
