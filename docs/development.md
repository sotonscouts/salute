# Development

To get started with development, you will need:

* GNU Make
* Python 3.11 or higher
* Poetry

Firstly, let's get the application running:

* `poetry install`
* `./manage.py migrate`
* `make dev` or `./manage.py runserver`

This will run Salute using a SQLite database, and you should be able to see it on `localhost:8000`.

## Generate Test Data

We have a command that will generate rudimentary test data.

* `./manage.py flush` - Delete all existing data
* `./manage.py generate_test_data` - Generate test data

The generation command will print login credentials for the admin interface at `localhost:8000/salute-backend/`