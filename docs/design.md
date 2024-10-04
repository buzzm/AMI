# Design Rant

Hello!  I am the design.

AMI has several important types such as Software, Instance, Endpoint, etc. but
there is a small, simple base class to take of common / boilerplate information.

## Item

| Field Name | Type |Notes |
|-|-|----------|
| owner	   | Actor    | the Actor accountable for the item |
| steward  | Actor    | the Actor responsible for operational maintenance, if any of the Item |
| vers  | int | integer version of the Item, starting at 1 |
| created  | datetime | timestamp of creation of this version |
| createdBy | Actor | Actor that manufactured this version |

In practice, the archive/analytical datastore contains *all* versions of items whereas
the operational datastore contains *only* the most recent.  By only keeping the
most recent we dramatically simplify queries and the general understanding
of the data.

## Version

Version is a blank node inside some classes; thus it is not a subclass of Item

| Field Name | Type |Notes |
|-|-|----------|
| majorVers  | int   | yep |
| minorVers  | int   | yep |
| patchVers  | int   | yep |
| alpha  | String   | yep |
| releaseDate  | datetime   | yep |


## Software (`rdfs:subClassOf Item`)

| Field Name | Type |Notes |
|-|-|----------|
| vendor  | Entity    | legal connection for the software |
| basename  | String    | Version-free name e.g. 'kafka' or 'oracle' |
| version  | Version  |  |
| linksWith  | Software  |  This is the biggie.  Dependency graph. This includes platform, like python3 |


## Data Message Exchange Protocol (DMEP)
| Field Name | Type |Notes |
|-|-|----------|
| type | String | I, IO, O, OI |
| req | Shape | A SHACL shape |
| response | Shape | A SHACL shape |
| protocol | String | http https 


## Endpoint 

| Field Name | Type |Notes |
|-|-|----------|
| port | int | 



## Software (`rdfs:subClassOf Item`)

| Field Name | Type |Notes |
|-|-|----------|
| vendor  | Entity    | legal connection for the software |
| basename  | String    | Version-free name e.g. 'kafka' or 'oracle' |
| version  | Version  |  |
| linksWith  | Software  |  This is the biggie.  Dependency graph. This includes platform, like python3 |








