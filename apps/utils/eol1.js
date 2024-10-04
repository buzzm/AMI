
function emit(c,emit=true) {
    var nn = 0;
    c.forEach(function(r) {
	    nn++;
	    if(emit == true) {
		//printjson(r);
		print(r);		
	    }
	});
    print("found " + nn); 
};

db = db.getSiblingDB("semantic");

collname = "eol";
coll = db[collname];

c = coll.aggregate([
    {$addFields: {
	daysDiff: {$cond:
		   [ {$and: [
		       {$eq:[{$type:'$releaseDate'},'date']},
		       {$eq:[{$type:'$eol'},'date']}
		      ]},
		     {$dateDiff: { 'startDate': '$releaseDate',
				'endDate': '$eol',
				   'unit':'year' }},
		     -1
		   ]}
    }}

    ,{$sort: {daysDiff: -1}}
    //,{$match: {daysDiff: -1}}
    
    ,{$limit: 100}
]);
emit(c);

