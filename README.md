# Installation - How to set up the dash up locally

## General
* Make virtual environment and install requirements
* Start webapp:
```bash
    python app.py
```

## Database
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