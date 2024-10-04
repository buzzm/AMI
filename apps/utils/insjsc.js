
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

var dd =
    {
    "type": "object",
    "properties": {
        "recentReviews": {
            "type": "object",
            "properties": {
                "reviewDate": {
                    "type": "string",
                    "format": "date-time"
                },
                "reviewerPhone": {
                    "type": "string"
                },
                "reviewerID": {
                    "type": "string"
                },
                "reviewerName": {
                    "type": "object",
                    "properties": {
                        "last": {
                            "type": "string"
                        },
                        "first": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "last",
                        "first"
                    ]
                },
                "text": {
                    "type": "string"
                }
            },
            "required": [
                "reviewDate",
                "reviewerPhone",
                "reviewerID",
                "text"
            ]
        },
        "amt": {
            "type": "integer"
        }
    },
    "required": [
        "amt"
    ]
    }


rc = db.ami5.insertOne({_id:"XXX", jsc:dd});
print(rc);
