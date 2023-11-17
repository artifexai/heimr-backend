#### Welcome to the Heimr Server

This provides the data and search APIs for the heimr app.

### Getting Started

To get started, clone the repo and install the requirements.

To work with a local database, you'll need to run the postgres service defined in docker-compose,
run the migration, and seed the data.

Pycharm has tools and run configurations that make this really easy. But for clarity,
here are the steps to set up and run the app from the commandline.

Start the database container:

```shell
docker-compose up db
```

Run the migration and seed the data:

```shell
alembic upgrade head
export PYTHONPATH=$(pwd)
python database/seed_db.py
```

Start the app:

```shell
uvicorn main:app --reload
```

### Running in Docker

To run the app in docker, you'll need to build the image and run the container.

If you are running locally on Apple Silicon, you'll need to specify the arm64 architecture by adding
`DOCKER_DEFAULT_PLATFORM=linux/amd64` to the environment variables.

To run the app in docker, run the following commands:

```shell
docker compose up --build api
```