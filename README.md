# PsyNamic Webapp Installation & Deployment Guide

This document describes how to set up the PsyNamic dashboard locally and how to deploy it on a UniBE VM.

The deployment documentation assumes that the VM is already set up and that DNS is configured to point to the VM's IP address. For details on how to set up a VM, see the [wiki entry](https://github.com/Ineichen-Group/wiki/blob/main/pages/how-to-vms.md)

It contains the following sections:
* [Local Development Setup (Non-Docker)](#local-development-setup-non-docker)
* [Local Development Setup (Docker)](#local-development-setup-docker)
* [Initial Deployment with Docker on UniBE VM](#initial-deployment-with-docker-on-unibe-vm)
* [Deployment of Updates](#deployment-of-updates)
* [Overview of Monitoring](#overview-of-monitoring)
* [Overview of the Repository Structure](#overview-of-the-repository-structure)


---

# Local Development Setup (Non-Docker)

## Create Virtual Environment and Install Dependencies

Create and activate a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Create Database

* Install [PostgreSQL](https://www.postgresql.org/download/linux/ubuntu/).
* Check if the installation was successful:

```bash
psql --version
```

Switch to the default PostgreSQL user:

```bash
sudo -i -u postgres
```

Enter the PostgreSQL command line:

```bash
psql
```

Create the database:

```sql
CREATE DATABASE psynamic;
```

Set a password for the PostgreSQL user:

```sql
ALTER USER postgres PASSWORD '<your password>';
```

Exit PostgreSQL:

```sql
\q
```

## Configure Environment Variables

Copy the example environment file:

```bash
cp .env.copy .env
```

Edit `.env` and add your local database configuration.

## Initialize and Populate Database

```bash
make db-init
```
---

# Local Development Setup (Docker)

* Install Docker and Docker Compose.
* Create a `.env` file based on `.env.copy` and set the database credentials.
* Build and start the application:

```bash
make build
make up
```

Access the application at:

http://localhost:8050

---

# Initial Deployment with Docker on UniBE VM

## Docker & Make

Make sure everything is up to date:

```bash
sudo apt list --upgradable
sudo apt update
sudo apt upgrade
```

Install `make` if it is not already installed:

```bash
sudo apt install make
```

Install Docker according to the [official Docker installation instructions for Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

Check if Docker is running:

```bash
sudo systemctl status docker
sudo docker run hello-world
```

Configure Docker to run as a non-root user according to the [Docker post-installation instructions](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user).

Configure Docker to start on boot so that the application restarts automatically when the server restarts. See the [Docker systemd instructions](https://docs.docker.com/engine/install/linux-postinstall/#configure-docker-to-start-on-boot-with-systemd).

Configure log rotation with `json-file` to limit the logs to recently generated ones by editing `/etc/docker/daemon.json` (create the file if it does not exist):

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Then restart Docker:

```bash
sudo systemctl restart docker
```

### Get the Repository

Clone the repository and navigate into it:

```bash
git clone git@github.com:Ineichen-Group/PsyNamic-Webapp.git
```

Set the environment variables in the `.env` file (copy from `.env.copy`) and edit accordingly.

Before deployment, disable debug mode in `app.py`:

```python
debug=False
```

## Configure Nginx and SSL

> Nginx is used as a reverse proxy between the public internet and the Dash application.

> The Dash application runs internally on port `8050`, while Nginx handles incoming HTTP/HTTPS traffic.

> Certbot is used to automatically obtain and renew SSL certificates from Let's Encrypt.

### Install Nginx and Certbot

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

### Configure Nginx

Create a new Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/psynamic
```

Add the following configuration and replace the domain if required:

```nginx
server {
    listen 80;
    server_name psynamic.dcr.unibe.ch;

    location / {
        proxy_pass http://0.0.0.0:8050/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

* Port `80` receives HTTP traffic.
* The Dash application runs on port `8050`.
* Nginx forwards incoming requests to the application.

### Enable the Site and Test Nginx

Create a symbolic link:

```bash
sudo ln -s /etc/nginx/sites-available/psynamic /etc/nginx/sites-enabled/
```

Test the configuration:

```bash
sudo nginx -t
```

Remove the default configuration:

```bash
sudo rm /etc/nginx/sites-enabled/default
```

Reload Nginx:

```bash
sudo systemctl reload nginx
```

## Obtain SSL Certificate with Certbot

```bash
sudo certbot --nginx -d psynamic.dcr.unibe.ch
```

After successful setup, the application should be available at:

https://psynamic.dcr.unibe.ch

This assumes that the DNS (ISPM) is correctly configured to point to the server's IP address.

## Build and Run the Application

Build and start the Docker containers:

```bash
make build
make up
```

Add the initial data dump and load:

```bash
make db-init
```

Copy models to `pipeline/models` and adjust `model_paths.json` accordingly.

---

## Setup Backup

### Install Required Packages

Install `rsync` and `cifs-utils`:

```bash
sudo apt update
sudo apt install cifs-utils rsync
```

### Create Mount Point and Set Permissions

```bash
sudo mkdir -p /mnt/research_storage
sudo chown sysadmin:sysadmin /mnt/research_storage
```

### Test Mounting the Research Storage

Replace the credentials with your own:

```bash
sudo mount -t cifs //resstore.unibe.ch/dcr_mds /mnt/research_storage \
  -o username=<username>,domain=campus,vers=3.0,sec=ntlmssp
```

You will be prompted for the password.

Verify the mount:

```bash
ls -lah /mnt/research_storage
```

Unmount again:

```bash
sudo umount /mnt/research_storage
```

### Create a Credentials File

To avoid entering the password every time, create a credentials file:

```bash
sudo nano /root/.research_storage_credentials
```

Add:

```ini
username=<your username>
password=<your password>
domain=campus
```

Secure the file:

```bash
sudo chmod 600 /root/.research_storage_credentials
sudo chown root:root /root/.research_storage_credentials
```

### Configure Persistent CIFS Mounting

Edit `fstab`:

```bash
sudo nano /etc/fstab
```

Add:

```fstab
//resstore.unibe.ch/dcr_mds /mnt/research_storage cifs credentials=/root/.research_storage_credentials,vers=3.0,sec=ntlmssp,uid=0,gid=0,file_mode=0600,dir_mode=0700,_netdev,nofail,x-systemd.automount,x-systemd.mount-timeout=30 0 0
```

### Test if the Mount Is Persistent

Unmount the share:

```bash
sudo umount /mnt/research_storage
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Mount all configured filesystems:

```bash
sudo mount -a
```

Verify:

```bash
findmnt /mnt/research_storage
```

Check the contents:

```bash
ls -lah /mnt/research_storage
```

### Test Backup Script

Make the backup script executable:

```bash
chmod +x backup.sh
```

Run it:

```bash
./backup.sh
```

The script should synchronize:

```text
data/
├── pubmed_fetch_results
├── predictions
└── relevant_studies
```

to:

```text
/mnt/research_storage/psynamic_data_backup/
```

---

## Log Rotation for Logs

Create the log directory:

```bash
mkdir -p log
```

Configure log rotation:

```bash
sudo nano /etc/logrotate.d/psynamic
```

Add:

```conf
/home/sysadmin/PsyNamic-Webapp/log/*.log {
    size 10M
    rotate 8
    compress
    delaycompress
    missingok
    notifempty
    su root sysadmin
}
```

Test the configuration:

```bash
sudo logrotate -d /etc/logrotate.d/psynamic
```

Optionally perform a real test rotation:

```bash
sudo logrotate -f /etc/logrotate.d/psynamic
```

Verify automatic logrotate scheduling:

```bash
systemctl status logrotate.timer
systemctl list-timers | grep logrotate
```

Your system will then automatically schedule log rotation; no cron entry is needed.

---

## Add Scheduled Jobs

Edit the cron settings:

```bash
sudo crontab -e
```

### Run the PubMed Pipeline

Every **Wednesday at 18:00**:

```cron
0 18 * * 3 cd /home/sysadmin/PsyNamic-Webapp && /usr/bin/make run-pipeline
```

> **Note:** If necessary, adjust the path to `make` (find it with `which make`).

This will create logs in:

```text
/home/sysadmin/PsyNamic-Webapp/log
```

### Monitor the Web Application

Every **5 minutes**:

```cron
*/5 * * * * cd /home/sysadmin/PsyNamic-Webapp && ./monitor.sh
```

The monitoring script:

* checks the Dash application
* checks Docker containers
* checks PostgreSQL connectivity
* writes logs to `/var/log/webapp_monitor.log`
* sends email alerts if a check fails

### Backup the Database

Every **Thursday at 03:00**:

```cron
0 3 * * 4 cd /home/sysadmin/PsyNamic-Webapp && /usr/bin/make backup
```

---


# Deployment of Updates

Commit local changes and push them to the repository:

```bash
git add .
git commit -m "Your commit message"
git push
```

Get the newest version of the repository and push it to the server:

```bash
git stash push -m "Keep production debug=False"
git pull
git stash pop
git push
```

Build and restart the application:

```bash
make build
make up
```

If the database schema has changed, reset the database and populate it with the initial and pipeline data:

```bash
make db-reset
```

---

# Overview of Monitoring

The following monitoring mechanisms are currently used:

* **`monitor.sh`**

  * Checks application availability
  * Checks Docker containers
  * Checks PostgreSQL connectivity
  * Sends email alerts on failures

* **UptimeRobot**

  * External uptime monitoring

* **apticron** (see the [wiki entry](https://github.com/Ineichen-Group/wiki/blob/main/pages/how-to-vms.md#setup-apticron) for details)

  * Monitors available system updates
  * Sends email notifications when updates are available

---

# Overview of the Repository Structure

The repository is organized as follows:

| Directory/File | Description |
|----------------|-------------|
| analysis | Contains scripts for data analysis for the publication |
| assets | Contains static assets such as images and CSS files |
| callbacks | Contains Dash callbacks for the web application |
| components | Contains reusable Dash components |
| data | Containes scripts and data for the PubMed fetch pipeline as well as prediction outputs |
| pages | Contains the Dash page layouts |
| pipeline | Contains the prediction pipeline scripts and models |
| styles | Contains color script |
| test | Contains test scripts for mainly the data processing |
| validation | Contains the scripts for validating the pubmed fetch pipeline |
| .env.copy | Example environment variable file |
| app.py | Main entry point for the Dash application |

Also consult Readme files in the subdirectories for more details.
