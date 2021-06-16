ACME
===
## Automated Collection and Manipulation of Email
*Create order where chaos reigns, your inbox ;)*

***This readme is still in revision as of June 14, 2021... you've been warned***

This project aims to automate away the tediouse and technical details involved with:
* Collecting email from your mail server -- done using imap (Internet Access Message Protocol), protocol [RFC822](https://datatracker.ietf.org/doc/html/rfc822) 
* Extracting the raw message text (or last message text if part of a thread) from the imap envlope structure
* Applying basic NLTK tools to the raw message text to produce lemmatized word-bags (a csr_matrix from the scikit-learn package)

I also aim to present this project as a sort of open-topped toolkit. Meaning it should allow users to grab only the sub-modules they need in order do any one of the above listed tasks. 

Ultimately, code in this repository is meant to reduce the number of steps the user (you) need to toake before you can get to the more interesting work of creating a custom tool for automated message classification, or simply conducting a personal analysis on how you communicate with friends and colleagues.  

This project has become a sort of hobby project for me, so I will continue to hack at it until I feel it has matured to the point that:
* A user can easily import this project from their own code and access only the tools they need
* There is a clear and thoroughly defined process for a community to extend the feature set of the project
* There is a clear and thoroughly defined process for guiding a user on how to supplement their own code in place of any sub-modules provided in this project.

#### [Project documentation](https://ryancpeters.github.io/ACME/) -- generated using doxygen

Prerequisites to using this application
---
## Accessing emails
The default configuration of this application is to use python's builtin `imaplib` package to access email. This means that in order for you to use this application on your own email account, you need to configure it to allow application access other than your normal browser access.

For the time being, I've only ever done this with a gmail account, though it should theoretically be portable accross all imap email hosts that support the imap protocol [`RFC822`](https://datatracker.ietf.org/doc/html/rfc822) (This should include most all modern email servers).

### For Gmail accounts
*As taken from google's help center, found here:* https://support.google.com/accounts/answer/185833

#### [Sign in with App Passwords]()
**Tip:** App Passwords aren’t recommended and are unnecessary in most cases. To help keep your account secure, use "Sign in with Google" to connect apps to your Google Account. 

An App Password is a 16-digit passcode that gives a less secure app or device permission to access your Google Account. App Passwords can only be used with accounts that have 2-Step Verification turned on.

#### [When to use App Passwords]()
**Tip:** iPhones and iPads with iOS 11 or up don’t require App Passwords. Instead use “Sign in with Google.”

If the app doesn’t offer “Sign in with Google,” you can either:

* Use App Passwords
* Switch to a more secure app or device

#### Create & use App Passwords
If you use [2-Step-Verification](https://support.google.com/accounts/answer/185839) and get a "password incorrect" error when you sign in, you can try to use an App Password.
   * When initially creating this project, I had to use an App Password. A ToDo item for this project is to investigate the steps for registering a custom app for use with Google's gmail api.

1. Go to your [Google Account](https://myaccount.google.com/).
1. Select Security.
1. Under "Signing in to Google," select App Passwords. You may need to sign in. If you don’t have this option, it might be because:
   1. 2-Step Verification is not set up for your account.
   1. 2-Step Verification is only set up for security keys.
   1. Your account is through work, school, or other organization.
   1. You turned on Advanced Protection.
1. At the bottom, choose Select app and choose the app you using and then Select device and choose the device you’re using and then Generate.
1. Follow the instructions to enter the App Password. The App Password is the 16-character code in the yellow bar on your device.
1. Tap Done.

Tip: Most of the time, you’ll only have to enter an App Password once per app or device, so don’t worry about memorizing it.

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
   * `git clone https://github.com/RyanCPeters/ACME.git`
   * `cd ACME`
   * the contents of the directory should look something like:
```
|- ACME/
	|- src/
		|- code files and stuff...
	|- .gitignore
	|- environment.yml
	|- README.md
	|- setup.py
```
4. use conda to set up and activate your virtual environment.
   * `conda env create -f ./environment.yml`
   * `conda activate acme_env`
      * optionally, you may inspect the packages available in the environment as follows:
         * `conda env export`
            * gives a verbose listing of packages and their versions
         * or you can call `conda env export --from-history`
            * This will tell you explicitly what the `environment.yml` file required.
5. Sanity check:
   * You should be in a conda activated terminal, with the active environment being our `acme_env` virtual environment.
   * You should also be in the `ACME` folder, which is the root of the project, 
   * The `setup.py` file should also be in the `ACME` folder.
6. Now we use `pip` to execute the `setup.py` file which creates a terminal entry-point for the application.
   * ` python -m pip install -e .`
      * tells python to run pip install with the `-e` flag that signals to use a local `setup.py` file.
      * we pass `.` to say that the `setup.py` file is located in the current working directory.
   * This will result in the creation of console entry-points to the program for easy command line interactions.
   * output should look something like this:
```
	$ python -m pip install -e .
	Obtaining file:///D:/GitHub_Remotes/shcool/ACME
	Installing collected packages: ACME
	  Running setup.py develop for ACME
	Successfully installed ACME
```
7. ~~We can now call the downloader command line entry point `collect_email` to get the default implementation of the downlaoder.~~
   	  * ~~The default implementation will download from the hard-coded email server, targeting the hard-coded account and password, and will cache the downloaded emails in the `*/EmailClassification/cache_files/` folder,~~
      * ~~Alternatively, you can call `collect_email /path/to/your/desired/cache/point`~~
         * ~~This custom cache directory will be created should it not already exist.~~
   * ~~If you would like to manually inspect the entire list of entry points the `setup.py` file created, see the keyword `entry_points` at the bottom of the `setup.py` file.~~
      * ~~This list is subject to change over time as further entry points are added.~~


## Overview of application's executional flow
The application's execution flow consists of three phases:
1. Email collection
   * Open/create email caching database on disk named `sql3_email.db`   
   * Download email header and generate unique message id
   * If id not in DB, download full message envelope (imap defined message structure) and cache add it to DB under derived id.
2. Message body parsing and extraction
   * Open/create email caching database on disk named `sql3_message_body.db`  
   * Open connection to `sql3_email.db` 
   * Load imap envelope from email db then decompose it into header, message text, and possible associated message thread members
   * The character set (encoding) of a given message can vary with the senders email service, so we convert all messages to be UTF-8.
      + In doing this we make sure to handle the more common problem characters not naturally covered by the UTF-8 encoding. (\u2014, \u2018, \u2019, and \ufeff)
    

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



