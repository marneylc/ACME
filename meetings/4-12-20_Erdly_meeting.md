My discussion objectives for today's meeting:
	* possibility of scheduling regular weekly/bi-weekly meetings through the end of quarter.
	* networking options for connecting with faculty or other potential advisors for the proper implementation of a secured database.
	* my absolute lack of experience in actually implementing a real backlog of any kind. 
	* presentation will be a video conference with live viewers. Should be mostly just like the in-person presentations.
	* discuss 485 material

Brent Lagesse for DB reach out in conjunction with Mark


This project will strive to follow a multi-tiered backlog structure.

The top tier (called the Portfolio Backlog), defines the broad strokes to the project; ie., the stakeholder's most basic needs from the project, and an outline of the developer's major checkpoints along the path to satisfying those needs. The items defined in this tier are not neccessarily tied to a required sequential ordering. Some times may be developed in parallel as part of the investigation of new approaches and solutions. This backlog can be considered a sort of outline that describes the project's areas of focus.

The middle tier (called the Solution Backlog) should define the core components to each item in the portfolio tier using "capabilities" and "enablers" and should provide an outline of the components needed for the subsequent development of the fine-grained Sprint Backlog. This backlog is where we identify obstacles, and then summarize appropriate solutions.

Finally, the finest detail backlog is the Sprint Backlog. This is where we will detail the constituent components required to actually implement the solutions to obstacles addressed in the Solution backlog.

```
## In the following backlogs, items marked with [x] are satisfactorilly completed for the objectives of this capstone project.
## 							  items marked with [o] are defined and in development 
##							  items marked with [-] are insufficiently defined as of yet to start development.
```

### Portfolio Backlog:
- [x] Research existing technologies.
	- There are several publications and a significant number of monetized (closed source) platforms that provide automated administration on
	  communication mediums such as emails. These sources will inform us where we should invest our efforts, as the subject is thoroughly discussed and the general consensus is that the task of creating an automated tool for identifying action items in an individual's email inbox is non-trivial, and has multiple potential solutions with each possessing a mixed bag of benefits and limitations.

- [o] Aggregate notes from research and synthesize objectives   
	- Objectives should must be chosen such that they can be "optimistically" reached, given the resources and tools 
	  available to the developer.

- [-] Develop Email access pipeline
	- This shall be a modular process that does 5 things: 
		1. Access online email client, generate a unique DB ID based upon imap message ID, and if not already present in the DB then it downloads the entire contents of the message to local machine and proceeds with data extraction.
		2. Extract message body content of the email, removing graphical elements for easier analysis of the written information, creating a container object for the message that is composed of the original message in its entirety along with the simplified message body we just created.
		3. Using the unique DB ID generated in step 1, add the container object created in step 2 to the DB.
		4. Provide an interface for applying classification tool set 
		5. Given a classification for a specific email, create a persistent mapping between that email and a searchable index of its labels. *Possibly even generate visual interface for the user to see similarly labeled emails grouped together; something like a Kanban board.*

### Solution Backlog:
- [o-] Build imap interface for email downloading, identification, and db entry functionality.
	- The DB component is likely going to be a SQLite DB implemented using the python package `sqlite3`. 
	- Email downloading, ID generation, and entry interface are otherwise implemented
- [o] Build Email content extraction functionality
	- Implementation for the extraction of an emails message body is still being sorted out, as there is a significant amount of variability in the way the information may be presented. Specifically, the image elements are automatically converted to strings without any proper identification marks when downloading via the included python imap package.
		* Further investigation into possible open source packages for this issue need to be pursued. 
- [o] Build Email caching DB
	- The DB component is likely going to be a SQLite DB implemented using the python package `sqlite3`. 
	- Details regarding the secure creation and maintenance of a sql database should be investigated and inquiry into possible  
	  professor contacts for advice should be discussed. 
- [o] Build classification integration interface
	- We need to define the scope of the internal tools that should be included/implemented 

### Sprint Backlog:
- [-] Develop storyboard for updated elements in the project


