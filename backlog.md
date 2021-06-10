backlog:
	* ~~Collect and evaluate publications on the topic of classifying emails into actionable and request-for-information~~
	* ~~Build automation pipeline for accessing inbox, and dowloading emails to local disk~~
		+ Note: project is opting to follow a minimal proof of concept approach that will initially only work with gmail imap server
	* ~~Build automation pipeline for extracting message contents from cached emails~~
		+ ~~Evaluate message's original character set and convert to utf-8~~
			- ~~Identify and correct characters from various expanded character sets which do not have an explicit representation in utf-8~~
		+ ~~Identify and extract base64 encoded image strings~~
		+ ~~Define OOP class structure that exposes the following:~~
			- ~~the original raw message data~~
			- ~~the extracted image strings~~
			- ~~the final utf-8 encoded message~~
	* ~~Build automation pipeline for NLP preprocessing~~
		+ ~~per-document tokenization~~
		+ ~~per-document lemmatization~~
		+ ~~per-document statistical extraction~~
	* ~~convert db entries that store python pickled objects as byte BLOBs into the more universal json string objects as TEXTs~~
	* Adapt data caching into a db pipeline.
		+ ~~convert `directory/file.pkl` based email caching into OOP styled table structures in `sqlite3` database.~~
		+ convert `directory/file.pkl` based message body caching into OOP styled table structures in `sqlite3` database.
		+ convert `directory/file.pkl` based keyword extraction caching into OOP styled table structures in `sqlite3` database.
	* Prep for practice presentation to Luke.
		+ ~~create slides that show hierarchical structure of project's sub-components~~
		+ ~~create slides that define third party tools used in project~~
		+ create slides that show a time-series roadmap of major project decisions:
			- ~~Initial intent: create a tool for automated classification of emails.~~
			- ~~redefined expectations surrounding email classification and a new shift of emphasis to the automation of peripheral operations required to engage in classification.~~
			- technical difficulties in ensuring proper text encoding against uncontrolled inputs.
			- and more...
		+ create slides that offer abstracted definition of the complexities involved with email classification.
		+ create appendix slides that cite sources and offer brief explanation of relevance to this project. 
	* Revise presentation and prepare second draft of presentation for Bill.

Future objectives for after colloquium:
	* Look into pushing DB to remote url host.
	* Look into blast: https://github.com/mosuka/blast  -- looks super cool!
	* Look into curl for data extraction.