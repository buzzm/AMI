

if [ "$MDB" == "" ] ; then
    printf "Set env var MDB with Atlas user:password\n"
    exit 1
fi
if [ "$OPENAI_API_KEY" == "" ] ; then
    printf "Set env var OPENAI_API_KEY\n"
    exit 1
fi
#if [ "$REACT_APP_AMI_URL" == "" ] ; then
#    printf "Set env var REACT_APP_AMI_URL\n"
#    exit 1
#fi


# EIP  Elastic IP is permanently bound to my subdomain!
#  	 50.112.191.129
AMI_HOST=https://ami.moschetti.org

CWD=`pwd`

#  jenaserver goes first:
(cd apps/jenacli ; nohup sh jena.runt jenaserver 5656 ami5 "mongodb://$MDB@test0-shard-00-00-rrpjf.mongodb.net:27017,test0-shard-00-01-rrpjf.mongodb.net:27017,test0-shard-00-02-rrpjf.mongodb.net:27017/semantic?ssl=true&replicaSet=test0-shard-0&authSource=admin&retryWrites=true&w=majority" > "$CWD/jenaserver.log" 2>&1 &)

printf "wait 3 seconds for jenaserver to come up because AMI server will check...\n"
sleep 3

#  next is amiserver:
source venv.1/bin/activate

(cd apps/amiserver ; nohup python3 -u app.py --api_key $OPENAI_API_KEY --ami_cpt ../../ami.cpt  --local_cpt ../../local.cpt --snippets ../../snippets.txt  --numctx 1 --log "$CWD/amiserver.log" > "$CWD/amis2.log"   2>&1 &)

#  last is node:
(cd apps/gui/ami-frontend/src ; PORT=3000 REACT_APP_TARG_URL=$AMI_HOST nohup npm start > "$CWD/node.log" 2>&1 &)




