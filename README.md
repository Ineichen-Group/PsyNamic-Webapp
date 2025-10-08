# Installation - How to set up the dash up locally


## NON-Docker setup
### General
* Make virtual environment and install requirements
* Start webapp:
```bash
    python app.py
```

### Database
* Install PostgreSQL
https://www.postgresql.org/download/linux/ubuntu/

* Setup database:
    * Install [PostgreSQL](https://www.postgresql.org/download/)
    * Check if installation was succesfull
    ```bash
    psql --version
    ```
    * Change to the default `postgres` user (or create a new one)
    ```bash
    sudo -i -u postgres
    ```
    * Enter the PostgreSQL Command Line
    ```bash
    psql
    ```
    * Create databse
    ```sql
    CREATE DATABASE psynamic;
    ```
    * Set a password for the default user
    ```sql
    ALTER USER postgres PASSWORD '<your password>';
    ```
    * rename `settings_copy.py` to `settings.py` and add your local database configs

* Create database schema via running `model.py` within the virtual evnironment
    ```bash
    python data/models.py
    ``` 

* Populate database by passing the new prediction and studies csv
    ```bash
    python data/populate.py -p data/predictions.csv -s data/studies.csv
    ```

* Delete database
    ```bash
    DROP DATABASE psynamic;
    ```

## Dealing with the database when deployed

* Make dump and load dump into database
    ```bash
    pg_dump -h localhost -U postgres -d psynamic -F c -f <dump_file>
    pg_restore --no-owner --dbname  <external_db_link> <dump_file>
    ```

* Add indexes to the database
    ```bash
    psql -d <database_name> -f data/indexes.sql
    ```
    
## Scheduled job to retrieve new papers
```bash
0 3 * * 1 docker compose run --rm pipeline
```

# Deployment on server

* Install docker according to: [https://docs.docker.com/engine/install/ubuntu/]https://docs.docker.com/engine/install/ubuntu/

    * Check if it's running with `sudo systemctl status docker` and `sudo docker run hello-world`
    * Configure to run docker with root priviliges: [https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)
    * Configure to start docker on boot (so that the application restarts automatically when the server restarts): [https://docs.docker.com/engine/install/linux-postinstall/#configure-docker-to-start-on-boot-with-systemd](https://docs.docker.com/engine/install/linux-postinstall/#configure-docker-to-start-on-boot-with-systemd)
    * Configure log rotation with json-file (limits the logs to recently generated ones) by editing in `/etc/docker/daemon.json` (create the file if it doesn't exist):
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

* Clone the repository and navigate into it
```bash
git clone git@github.com:Ineichen-Group/PsyNamic-Webapp.git
``` 

* Set envs in `.env` file (copy from `.env.exp`) and edit accordingly

* Set up nginx as a reverse proxy with SSL
    What is this and why do we need it?

    Nginx is a web server and reverse proxy that forwards requests from the internet to the web application running on a specific port. It enables HTTP/HTTPS handling, load balancing, and security features.

    Certbot is a tool that automates the process of obtaining and renewing SSL certificates from Let's Encrypt. SSL certificates are used to encrypt data transmitted between the user's browser and the web server, ensuring secure communication.

    
    * Install nginx and certbot
    ```bash
    sudo apt install nginx
    ```

    * Configure new nginx configs
    ```bash
    sudo nano /etc/nginx/sites-available/psynamic
    ```
    Paste the following (replace with your domain):
    ```
    server {
        listen 80;
        server_name psynamic.dcr.unibe.ch;

        location / {
            proxy_pass http://localhost:8050;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    ```
    -> port 80 is for HTTP traffic, web app is running on port 8050

    * Enable the site and test nginx
    ```bash
    sudo ln -s /etc/nginx/sites-available/psynamic /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx
    ```
    * Obtain SSL certificate with certbot
    ```bash
        sudo apt install certbot python3-certbot-nginx
        sudo certbot --nginx -d psynamic.dcr.unibe.ch
    ```

* Build and start the docker containers
```bash
make build
make up
```

* Add inital data dump and load
```bash
make load-dump
make load-indexes
```

* Visit https://psynamic.dcr.unibe.ch

* Copy models to and adjust `model_paths.json` accordingly

# Other useful commands
* Check if DNS is working (replace with your domain)
```bash
nslookup psynamic.dcr.unibe.ch
``` 
