# SC3020-Project-2
## Instructions before running program
1. Edit database connection variables (database name, user, password, host, port) in the .env file as per own system settings
2. Ensure that all external libaries and toolkits used (PyQt6, PyQt6_sip, psycopg2, python-dotenv) have been installed. You may use the command below to assist you.

```shell
pip install -r requirements.txt
```
3. Download and Install Graphviz:
  1. Step 1 : Go to the [Graphviz download page](https://graphviz.org/download/) and download the installer for your operating system. 
Run the installer and complete the installation. Make note of the installation directory, which is typically something like: C:\Program Files\Graphviz
  2. Step 2: Add Graphviz to the System PATH
    * After installing Graphviz, you need to add its bin directory to your system PATH so that dot and other executables are accessible globally.
    * Open Environment Variables: Press Win + R, type sysdm.cpl, and press Enter. This will open the System Properties window.
    * Go to the Advanced tab and click Environment Variables.
    * Edit the PATH Variable:
      * In the Environment Variables window, under System variables, locate and select the Path variable, then click Edit.
      * In the Environment Variables window, under System variables, locate and select the Path variable, then click Edit.
      * Click New and add the path to Graphviz's bin directory. For example: C:\Program Files\Graphviz\bin

4. Execute the program. You may do so with the following command.

```shell
python project.py
```