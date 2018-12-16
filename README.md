![](https://github.com/QualiSystems/cloudshell-shells-documentaion-templates/blob/master/cloudshell_logo.png)

# **VyOS Deployment App 2G Shell**  

Release date: May 2018

Shell version: 1.0.0

Document version: 1.0

# In This Guide

* [Overview](#overview)
* [Downloading the Shell](#downloading-the-shell)
* [Importing and Configuring the Shell](#importing-and-configuring-the-shell)
* [Updating Python Dependencies for Shells](#updating-python-dependencies-for-shells)
* [Typical Workflows](#typical-workflows)
* [References](#references)

# Overview
A shell integrates a device model, application or other technology with CloudShell. A shell consists of a data model that defines how the device and its properties are modeled in CloudShell, along with automation that enables interaction with the device via CloudShell.

### Networking Shells
CloudShell's networking shells provide L2 connectivity between resources and/or private cloud Apps.

### **VyOS Deployment App 2G Shell**
**VyOS Deployment App 2G** shell provides you with connectivity and management capabilities such as device structure discovery and power management for the **VyOS** deployment App. The device is provided as a virtual machine within a vCenter App.

For more information on the **VyOS** operating system, see the official **VyOS** product documentation.

### Standard version
**VyOS Deployment App 2G** shell is based on the CloudShell Deployed App Standard 1.0.3.

### Requirements

Release: **VyOS Deployment App 2G Shell**

▪ VyOS versions: 1.1.8 and above

▪ CloudShell versions: 8.2 and above

▪ VyOS Image versions: 1.1.8 and above

**Note:** If your CloudShell version does not support this shell, you should consider upgrading to a later version of CloudShell or contact customer support.

### Data Model

The shell's data model includes all shell metadata, families, and attributes.

#### **VyOS Deployment App 2G Shell Families and Models**

The families and models are listed in the following table:

|Family|Model|Description|
|:---|:---|:---|
|CS_GenericAppFamily|VyOS|VyOS deployed image|
|CS_Port|Vyos.GenericVPort|VyOS deployed image port|

#### **VyOS Deployment App 2G Shell Attributes**

The attribute names and types are listed in the following table:

|Attribute|Type|Default value|Description|
|:---|:---|:---|:---|
|Configuration File|String||Path to the configuration file, including the configuration file name. Path should include the protocol type, for example *tftp://10.10.10.10/asdf*.|
|Enable SSH|Boolean|True|Enable SSH on the deployed VM through vCenter.|
|User|Boolean|String|Username for the deployed VyOS virtual machine.|
|Password|Password||Password for the deployed VyOS virtual machine.|

#### **VyOS Deployment App 2G Port Attributes**

The attribute names and types are listed in the following table:

|Attribute|Type|Description|
|:---|:---|:---|
|Logical Name|String|Port's logical name in the test configuration|
|Requested vNIC|String|VNic number from vCenter|
|MAC Address|String|Port's MAC address|

### Automation
This section describes the automation (drivers) associated with the data model. The shell’s driver is provided as part of the shell package. There are two types of automation processes, Autoload and Resource.  Autoload is executed when creating the resource in the **Inventory** dashboard, while resource commands are run in the sandbox.

#### VyOS Deployment App 2G shell
|Command|Description|
|:-----|:-----|
|Autoload|Discovers the chassis, its hierarchy and attributes when creating the resource. The command can be rerun in the Inventory dashboard and not in the sandbox, as for other commands.|
|Restore|Enter the restore path string.|
|Save|Enter the save folder_path string.|

# Downloading the Shell
The **VyOS Deployment App 2G** shell is available from the [Quali Community Integrations](https://community.quali.com/integrations) page. 

Download the files into a temporary location on your local machine. 

The shell comprises:

|File name|Description|
|:---|:---|
|VyOS Deployment App Shell 2G.zip|VyOS Deployment App 2G shell package|
|vyos-deployment-app-offlinepackages-1.0.0.zip|Shell Python dependencies (for offline deployments only)|
|VyOS.Sandbox.Setup.1.0.1zip|CloudShell reservation setup script |

# Importing and Configuring the Shell
This section describes how to import the **VyOS Deployment App 2G** shell and configure and modify the shell’s devices.

### Importing the shell into CloudShell

**To import the shell into CloudShell:**
  1. Make sure you have the shell’s zip package. If not, download the shell from the [Quali Community's Integrations](https://community.quali.com/integrations) page.
  
  2. In CloudShell Portal, as Global administrator, open the **Manage – Shells** page.
  
  3. Click **Import**.
  
  4. In the dialog box, navigate to the shell's zip package, select it and click **Open**.

The shell is displayed in the **Shells** page and can be used by domain administrators in all CloudShell domains to create new Deployed Apps, as explained in [Add Apps](https://help.quali.com/Online%20Help/9.0/Portal/Content/CSP/LAB-MNG/Sndbx-Use-Apps.htm#Adding). 

### Offline installation of a shell

**Note:** Offline installation instructions are relevant only if CloudShell Execution Server has no access to PyPi. You can skip this section if your execution server has access to PyPi. For additional information, see the online help topic on offline dependencies.

In offline mode, import the shell into CloudShell and place any dependencies in the appropriate dependencies folder. The dependencies folder may differ, depending on the CloudShell version you are using:

* For CloudShell version 8.3 and above, see [Adding Shell and script packages to the local PyPi Server repository](#adding-shell-and-script-packages-to-the-local-pypi-server-repository).

* For CloudShell version 8.2, perform the appropriate procedure: [Adding Shell and script packages to the local PyPi Server repository](#adding-shell-and-script-packages-to-the-local-pypi-server-repository) or [Setting the python pythonOfflineRepositoryPath configuration key](#setting-the-python-pythonofflinerepositorypath-configuration-key).

### Adding shell and script packages to the local PyPi Server repository
If your Quali Server and/or execution servers work offline, you will need to copy all required Python packages, including the out-of-the-box ones, to the PyPi Server's repository on the Quali Server computer (by default *C:\Program Files (x86)\QualiSystems\CloudShell\Server\Config\Pypi Server Repository*).

For more information, see [Configuring CloudShell to Execute Python Commands in Offline Mode](http://help.quali.com/Online%20Help/9.0/Portal/Content/Admn/Cnfgr-Pyth-Env-Wrk-Offln.htm?Highlight=Configuring%20CloudShell%20to%20Execute%20Python%20Commands%20in%20Offline%20Mode).

**To add Python packages to the local PyPi Server repository:**
  1. If you haven't created and configured the local PyPi Server repository to work with the execution server, perform the steps in [Add Python packages to the local PyPi Server repository (offlinemode)](http://help.quali.com/Online%20Help/9.0/Portal/Content/Admn/Cnfgr-Pyth-Env-Wrk-Offln.htm?Highlight=offline%20dependencies#Add). 
  
  2. For each shell or script you add into CloudShell, do one of the following (from an online computer):
      * Connect to the Internet and download each dependency specified in the *requirements.txt* file with the following command: 
`pip download -r requirements.txt`. 
     The shell or script's requirements are downloaded as zip files.

      * In the [Quali Community's Integrations](https://community.quali.com/integrations) page, locate the shell and click the shell's **Download** link. In the page that is displayed, from the Downloads area, extract the dependencies package zip file.

3. Place these zip files in the local PyPi Server repository.
 
### Setting the python PythonOfflineRepositoryPath configuration key
Before PyPi Server was introduced as CloudShell’s python package management mechanism, the `PythonOfflineRepositoryPath` key was used to set the default offline package repository on the Quali Server machine, and could be used on specific Execution Server machines to set a different folder. 

**To set the offline python repository:**
1. Download the *vyos-deployment-app-offlinepackages-1.0.0.zip* file, see [Downloading the Shell](#downloading-the-shell).

2. Unzip it to a local repository. Make sure the execution server has access to this folder. 

3.  On the Quali Server machine, in the *~\CloudShell\Server\customer.config* file, add the following key to specify the path to the default python package folder (for all Execution Servers):  
	`<add key="PythonOfflineRepositoryPath" value="repository 
full path"/>`

4. If you want to override the default folder for a specific Execution Server, on the Execution Server machine, in the *~TestShell\Execution Server\customer.config* file, add the following key:  
	`<add key="PythonOfflineRepositoryPath" value="repository 
full path"/>`

5. Restart the Execution Server.

### Configuring a new App
This section explains how to create an App template for the **VyOS Deployment App** to enable network connectivity between endpoints in the sandbox.

1. In CloudShell Portal, as Global administrator, open the **Manage – Apps** page.

2. Click **Add**.

3. Select any type of vCenter deployment option, suc as **vCenter Clone VM From VM**, **vCenter VM from Template**, **vCenter VM from Image**, etc. This shell is hardcoded to support vCenter only.

4. Enter the **Name** of the App and click **Create**.

5. In the **Deployment Paths** tab, select the **Cloud Provider** and enter the **vCenter VM** to be used in VM creation. It should include the full path from the datacenter and template name, for example *QualiFolder/VM121*.
![](https://github.com/QualiSystems/VyOS-Deployment-App-Shell-2G/blob/master/vyos_deployment_app_2g_deployment_paths.PNG)

6. In the **App Resource** tab, select the **Vyos** shell. You must specify the **User** and **Password** of the shell. All other attributes are optional.

	**Note:** Contact your Admin to obtain the correct credentials to set on the deployed App shell. They are generally provided  along with the VM image.  

	<br>![](https://github.com/QualiSystems/VyOS-Deployment-App-Shell-2G/blob/master/vyos_deployment_app_2g_app_resource.PNG)

7. Click **Done**.

The App is ready to be used in CloudShell sandboxes. A dedicated VM will be created once the App is deployed in a sandbox. Note that you can deploy multiple instances of the same App in the sandbox.


### Configuring the setup script
This section explains how to add the setup script for the **VyOS Deployment App 2G** shell.

**To add the setup script:**
1. Log in to CloudShell Portal as administrator of the relevant domain.

2. Go to the **Manage** dashboard and click **Scripts>Blueprint**.

3. Click **Add New Script**. From the list, select the downloaded setup script *VyOS.Sandbox.Setup.1.0.1.zip* and click **Open**.

4. Click **Edit** and change the **Script Type** to **Setup**.

5. Click **Save**.

# Updating Python Dependencies for Shells
This section explains how to update your Python dependencies folder. This is required when you upgrade a shell that uses new/updated dependencies. It applies to both online and offline dependencies.

### Updating offline Python dependencies
**To update offline Python dependencies:**
1. Download the latest Python dependencies package zip file locally.

2. Extract the zip file to the suitable offline package folder(s). 

3. Terminate the shell’s instance, as explained [here](http://help.quali.com/Online%20Help/9.0/Portal/Content/CSP/MNG/Mng-Exctn-Srv-Exct.htm#Terminat). 

### Updating online Python dependencies
In online mode, the execution server automatically downloads and extracts the appropriate dependencies file to the online Python dependencies repository every time a new instance of the driver or script is created.

**To update online Python dependencies:**
* If there is a live instance of the shell's driver or script, terminate the shell’s instance, as explained [here](http://help.quali.com/Online%20Help/9.0/Portal/Content/CSP/MNG/Mng-Exctn-Srv-Exct.htm#Terminat). If an instance does not exist, the execution server will download the Python dependencies the next time a command of the driver or script runs.

# Typical Workflows 

#### *Deploying the VyOS Deployment App 2G shell* 
1. Log in to CloudShell Portal and create a new blueprint (**Blueprint Catalog>Create Blueprint**).

2. Give the blueprint a name.

3. Add the **VyOS Deployment App** to the blueprint.
	* Open the **App/Service** menu.
	* Drag and drop the **VyOS Deployment App 2G** App to the canvas.

4. Update the blueprint setup script.
	* In the **Blueprint** menu, open **Properties**.
	* In the **Scripts** section, select the **Default Sandbox Setup 2.0** script and click the trash icon to the right of the script.
	* Click **Add Scripts**.
	* Select the **VyOS.Sandbox.Setup.1.0.1**.
	* Click **Done**.

5. Reserve the blueprint.

# References
To download and share integrations, see [Quali Community's Integrations](https://community.quali.com/integrations). 

For instructional training and documentation resources, see the [Quali University](https://www.quali.com/university/).

To suggest an idea for the product, see [Quali's Idea box](https://community.quali.com/ideabox). 

To connect with Quali users and experts from around the world, ask questions and discuss issues, see [Quali's Community forums](https://community.quali.com/forums). 

