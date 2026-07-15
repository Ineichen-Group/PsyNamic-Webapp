# PsyNamic Webapp Installation & Deployment Guide

This document describes how to set up the PsyNamic dashboard locally and how to deploy it on a UniBE VM.

---

# Local Development Setup (Non-Docker)

## General Setup

### Create virtual environment and install dependencies

Create and activate a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Database

- Install [PostgreSQL](https://www.postgresql.org/download/linux/ubuntu/)

- Check if installation was succesfull

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

### Configure Environment Variables

Copy the example environment file:

```bash
cp .env.copy .env
```

Edit `.env` and add your local database configuration.

### Initialize and Populate Database and Indexes

- Populate initial database content:

```bash
./init_db.sh
```

- Populate all data retrieved automatically by the pipeline:

```bash
python -m data.populate --all
```

- Add database indexes:

```bash
psql -d psynamic -f data/indexes.sql
```

### Dealing with the database when deployed

- Make dump and load dump into database

  ```bash
  pg_dump -h localhost -U postgres -d psynamic -F c -f <dump_file>
  pg_restore --no-owner --dbname  <external_db_link> <dump_file>
  ```

# Deployment with Docker on UniBE VM

## Basic Setup: Make and Docker

- Make sure everything is up to date

```bash
sudo apt list --upgradable
sudo apt update
sudo apt upgrade
```

- Install make if not already installed

```bash
sudo apt install make
```

- Install docker according to: [https://docs.docker.com/engine/install/ubuntu/]https://docs.docker.com/engine/install/ubuntu/
  - Check if it's running with `sudo systemctl status docker` and `sudo docker run hello-world`
  - Configure to run docker with root priviliges: [https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)
  - Configure to start docker on boot (so that the application restarts automatically when the server restarts): [https://docs.docker.com/engine/install/linux-postinstall/#configure-docker-to-start-on-boot-with-systemd](https://docs.docker.com/engine/install/linux-postinstall/#configure-docker-to-start-on-boot-with-systemd)
  - Configure log rotation with json-file (limits the logs to recently generated ones) by editing in `/etc/docker/daemon.json` (create the file if it doesn't exist):

  ```json
  {
    "log-driver": "json-file",
    "log-opts": {
      "max-size": "10m",
      "max-file": "3"
    }
  }
  ```

  Then restart docker with `sudo systemctl restart docker`

## Deployment Steps

- Clone the repository and navigate into it

```bash
git clone git@github.com:Ineichen-Group/PsyNamic-Webapp.git
```

- Set envs in `.env` file (copy from `.env.copy`) and edit accordingly

- Before deployment, disable debug mode in `app.py`:

```python
debug=False
```

### Configure Nginx and SSL

> Nginx is used as a reverse proxy between the public internet and the Dash application.
> The Dash application runs internally on port `8050`, while Nginx handles incoming HTTP/HTTPS traffic.
> Certbot is used to automatically obtain and renew SSL certificates from Let's Encrypt.

- Install nginx and certbot

  ```bash
  sudo apt install nginx certbot python3-certbot-nginx
  ```

- Configure new nginx configs

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

  - Port `80` receives HTTP traffic.
  - The Dash application runs on port `8050`.
  - Nginx forwards incoming requests to the application.

- Enable the site and test nginx
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

- Obtain SSL certificate with certbot

  ```bash
  sudo certbot --nginx -d psynamic.dcr.unibe.ch
  ```

  After successful setup, the application should be available at:

  ```
  https://psynamic.dcr.unibe.ch
  ```

### Build and Run the Application

- Build and start the docker containers

  ```bash
  make build
  make up
  ```

- Add inital data dump and load

  ```bash
  make db-init
  ```

- Copy models to `pipeline\models` and adjust `model_paths.json` accordingly

### Data Backup

- install rsync and cifs-utils

  ```bash
  sudo apt update
  sudo apt install cifs-utils rsync
  ```

- create mount point and set permissions

  ```bash
    sudo mkdir -p /mnt/research_storage
    sudo chown sysadmin:sysadmin /mnt/research_storage
  ```

- test mounting the research storage (replace with your credentials)

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

- cretae a credentials file to avoid entering the password every time

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

- configure persistent cifs mounting
  Edit fstab:

  ```bash
  sudo nano /etc/fstab
  ```

  Add:

  ```fstab
  //resstore.unibe.ch/dcr_mds /mnt/research_storage cifs credentials=/root/.research_storage_credentials,vers=3.0,sec=ntlmssp,uid=0,gid=0,file_mode=0600,dir_mode=0700,_netdev,nofail,x-systemd.automount,x-systemd.mount-timeout=30 0 0
  ```

- test if the mount is persistent
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

  Check contents:

  ```bash
  ls -lah /mnt/research_storage
  ```

- test backup script

  ```bash
  chmod +x backup.sh
  ./backup.sh
  ```

  The script should synchronize:

  ```
  data/
  ├── pubmed_fetch_results
  ├── predictions
  └── relevant_studies
  ```

  to:

  ```
  /mnt/research_storage/psynamic_data_backup/
  ```

# Scheduled jobs

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
    weekly
    size 10M
    rotate 8
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

Test the configuration:

```bash
sudo logrotate -d /etc/logrotate.d/psynamic
```

Open the crontab:

```bash
crontab -e
```

Add the following entries.

## Run the PubMed Pipeline

Every **Wednesday at 18:00**:

```cron
0 18 * * 3 cd /home/sysadmin/PsyNamic-Webapp && /usr/bin/make run-pipeline```

> **Note:** If necessary, adjust the path to `make` (find it with `which make`).

This will create logs in `/home/sysadmin/PsyNamic-Webapp/log

## Monitor the Web Application

Every **5 minutes**:

```cron
*/5 * * * * cd /home/sysadmin/PsyNamic-Webapp && ./monitor.sh
```

The monitoring script:

- checks the Dash application, Docker containers, and PostgreSQL,
- writes logs to `/var/log/webapp_monitor.log`,
- sends email alerts if a check fails.

## Backup the Database

Every **Thursday at 03:00**:

```cron
0 3 * * 4 cd /home/sysadmin/PsyNamic-Webapp && /usr/bin/make backup
```

# Monitoring

The following monitoring mechanisms are currently used:

- `monitor.sh`
  - Checks application availability
  - Checks Docker containers
  - Checks PostgreSQL connectivity
  - Sends email alerts on failures

- **UptimeRobot**
  - External uptime monitoring

- **apticron** (s. [wiki entry](https://github.com/Ineichen-Group/wiki/blob/main/pages/how-to-vms.md#setup-apticron) for details)
  - Monitors available system updates
  - Sends email notifications when updates are available

# Common errors

`entrypoint.sh": permission denied: unknown`

This error usually occurs when the `entrypoint.sh` script does not have the executable permission. To fix this, you can run the following command in the terminal:

```bash
chmod +x entrypoint.sh
docker compose build --no-cache
```

# Other useful commands

- Check if DNS is working (replace with your domain)

```bash
nslookup psynamic.dcr.unibe.ch
```
