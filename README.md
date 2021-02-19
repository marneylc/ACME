# EmailClassification
Create order where chaos reigns, your inbox ;)


Isolated downloader demonstration steps:

1. install Anaconda's `Miniconda` console tool for minimalistic footprint virtual environment manager.
   * go to...
      *  https://docs.conda.io/en/latest/miniconda.html
   * choose your installation process and follow the docs they provide.
2. launch the resulting conda terminal (In windows this is a specific powershell/cmd terminal, this may vary on *nix systems)
3. clone this repository to your local machine, then cd into that cloned directory.
   * the contents should look something like:
   ```
   		|- EmailClassification
   			|- Presentation_resources
   				|- ignorable stuffs for now
   			|- src
   				|- code files and stuff...
   			|- .gitignore
   			|- README.md
   			|- environment.yml     			# this environment file is for full classification pipeline
   			|- downloader_environment.yml   # this environment file gives minimal footprint for downloading and caching emails.
   ```
4. use conda to set up and activate your virtual environment.
   * `conda env install -f ./downloader_environment.yml`
   * `conda activate email_downlaoder_env`
	   