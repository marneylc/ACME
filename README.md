# EmailClassification
Create order where chaos reigns, your inbox ;)


Isolated downloader demonstration steps:

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
	|- downloader_environment.yml   # this environment file gives minimal footprint for downloading and caching emails.
	|- environment.yml     			# this environment file is for full classification pipeline
	|- README.md
	|- setup.py
   ```
4. use conda to set up and activate your virtual environment.
   * ` conda env create -f ./downloader_environment.yml`
   * `conda activate email_downlaoder_env`
      * optionally, you may inspect the packages available in the environment as follows:
         * `conda env export`
            * gives a verbose listing of packages and their versions
         * or you can call `conda env export --from-history`
            * This will tell you explicitly what the `downloader_environment.yml` file required.
5. 