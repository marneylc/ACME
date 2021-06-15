ACME
===
## Automated Collection and Manipulation of Email
*Create order where chaos reigns, your inbox ;)*

This project aims to automate away the tediouse and technical details involved with 

**This readme is still in revision as of June 14, 2021... you've been warned**

Prerequisites to using this application
---
## Accessing emails
The default configuration of this application is to use python's builtin `imaplib` package to access email. This means that in order for you to use this application on your own email account, you need to configure it to allow application access other than your normal browser access.

For the time being, I've only ever done this with a gmail account, though it should theoretically be portable accross all imap email hosts that support imap protocol [`RFC822`](https://datatracker.ietf.org/doc/html/rfc822) (This should include most all modern email servers).

### For Gmail accounts
*As taken from google's help center, found here:* https://support.google.com/accounts/answer/3466521

###### Manage third-party apps & services with access to your account
To help you safely share your data, Google lets you give third-party apps and services access to different parts of your Google Account. Third-party apps and services are created by companies or developers that aren’t Google.

For example, you may download an app that helps you schedule workouts with friends. This app may request access to your Google Calendar and Contacts to suggest times and friends for you to meet up with.

###### Sharing your Google data with Apps
Learn about how you can share your Google data with apps to make your life easier -- and what you can do to protect your personal information.

###### Review what a third party can access
You can review the type of account access a third party has as well as the Google services it has access to.
1. Go to the [Security section of your Google Account](https://myaccount.google.com/security).
2. Under “Third-party apps with account access,” select Manage third-party access.
   * As you scroll down the window after following the link, you should see a section like this on the right:
    ![./readme_support_images/third_party_apps_image1.png]
3. Select the app or service you want to review.

### For non-Gmail accounts
ToDo: Experiment with non-gmail accounts and update this portion of the guide once a proper procedure is confirmed.

## Accessing cached data
### Database details
We are using the python builtin package `sqlite3` to manage our databases where we cache persistent message and associated analysis data to disk.

We are also maintaining 3 seperate databases over the course of the applications execution. We chose to do this in order to maintain a higher level of encapsulation between the major execution steps of the application. Thus ensuring the end user can easily treat this application as an adaptable toolkit that they can customize to their unique needs as they explore the data potentials of their email inbox.

Installation instructions
---

1. install Anaconda's `Miniconda` console tool for minimalistic footprint virtual environment manager.
   * go to...
      *  https://docs.conda.io/en/latest/miniconda.html
   * choose your installation process and follow the docs they provide.
2. launch the resulting conda terminal (In windows this is a specific powershell/cmd terminal, this may vary on \*nix systems)
3. clone this repository to your local machine, then cd into that cloned directory.
   * the contents should look something like:
```
|- EmailClassification
	|- Presentation_resources
		|- ignorable stuffs for now
	|- src
		|- code files and stuff...
	|- .gitignore
	|- environment.yml     			# this environment file is for full classification pipeline
	|- README.md
	|- setup.py
```
4. use conda to set up and activate your virtual environment.
   * ` conda env create -f ./environment.yml`
   * `conda activate email_downlaoder_env`
      * optionally, you may inspect the packages available in the environment as follows:
         * `conda env export`
            * gives a verbose listing of packages and their versions
         * or you can call `conda env export --from-history`
            * This will tell you explicitly what the `downloader_environment.yml` file required.
5. Sanity check:
   * You should be in a conda activated terminal, inside of the `email_downlaoder_env` virtual environment.
   * You should also be in the `EmailClassification` folder, which is the root of the project, 
   * The `setup.py` file should also be in the `EmailClassification` folder.
6. Now we have `pip` use the `setup.py` file to modify the environment.
   * ` python -m pip install -e .`
      * tells python to run pip install with the `-e` flag that signals to use a local `setup.py` file.
      * we pass `.` to say that the `setup.py` file is located in the current working directory.
   * This will result in the creation of console entry-points to the program for easy command line interactions.
   * output should look something like this:
```
	$ python -m pip install -e .
	Obtaining file:///D:/GitHub_Remotes/shcool/EmailClassification
	Installing collected packages: EmailClassification
	  Running setup.py develop for EmailClassification
	Successfully installed EmailClassification
```
7. We can now call the downloader command line entry point `email_download` to get the default implementation of the downlaoder.
   	  * The default implementation will download from the hard-coded email server, targeting the hard-coded account and password, and will cache the downloaded emails in the `*/EmailClassification/cache_files/` folder,
      * Alternatively, you can call `email_download /path/to/your/desired/cache/point`
         * This custom cache directory will be created should it not already exist.
   * If you would like to manually inspect the entire list of entry points the `setup.py` file created, see the keyword `entry_points` at the bottom of the `setup.py` file.
      * This list is subject to change over time as further entry points are added.


## Overview of application's executional flow
The application's execution flow consists of three phases:
1. Email collection
   * Open/create email caching database on disk named `sql3_email.db`   
   * Download email header and generate unique message id
   * If id not in DB, download full message envelope (imap defined message structure) and cache add it to DB under derived id.
2. Message body parsing and extraction
   * Open/create email caching database on disk named `sql3_message_body.db`  
   * Open connection to `sql3_email.db` 
   * Decompose message structure into header, body, and possible associated message thread
   *  


Conceptual elements for possible classification tools:
===

### Speach Act Theory
The following excerpts were extracted from [Classifying Action Items for Semantic Email](./references/Classifying_Action_Items_for_Semantic_Email.pdf)

> ...This model is based on aspects of the Speech Act Theory (Searle, 1969), which states that every utterance implies an action by the speaker with varying effects on both the speaker and the hearer. When applied to electronic conversations, the sender and the recipient perform the roles of the speaker/hearer whereas textual phrases function as utterances. Action items in the model consist of three parameters:
>
> * Action – what is being performed e.g. a request, a notification or an assignment
> * Object – the object of the action e.g. a request for a meeting
> * Subject – the subject/agent of the object if applicable e.g. who will/would attend the meeting
>
> Actions consist of Request – an action requiring a reply from the recipient (e.g. a question); Assign – an action requiring an activity but no reply (e.g. an order or a commitment); Suggest – an action involving an optional activity; and Deliver – the action of delivering data. Objects are categorised into Activities (Task and Event) and Data (Information and Resource). The subject parameter is only applicable to activities (being the task performer(s) or the event participant(s) – i.e. Sender, Recipient, Both). Thus, a request for permission to attend an event is represented as a (Request, Event, Sender), an order to perform a joint task as an (Assign, Task, Both), and a request for information can be represented as a (Request, Information, Ø). The basic 22 combinations of these parameters (i.e. the email action items) together with a brief description are shown in Fig. 1.
>
> ![Example Diagram](./presentaion_resources/Speach_Act_Theory_structure.png "Figure 1: The 22 action item instances for the classification task, with a short description")
> <figcaption>Figure 1: The 22 action item instances for the classification task, with a short description</figcaption>



