[![Build Status](https://travis-ci.org/frol/flask-restplus-server-example.svg)](https://travis-ci.org/frol/flask-restplus-server-example)
[![Coverage Status](https://coveralls.io/repos/frol/flask-restplus-server-example/badge.svg?branch=master&service=github)](https://coveralls.io/github/frol/flask-restplus-server-example?branch=master)
[![Codacy Coverage Status](https://api.codacy.com/project/badge/coverage/b0fc91ce77d3437ea5f107c4b7ccfa26)](https://www.codacy.com/app/frolvlad/flask-restplus-server-example)
[![Codacy Quality Status](https://api.codacy.com/project/badge/grade/b0fc91ce77d3437ea5f107c4b7ccfa26)](https://www.codacy.com/app/frolvlad/flask-restplus-server-example)


RESTful API Server Example
==========================

This project showcases my vision on how the RESTful API server should be
implemented.

The goals that were achived in this example:

* RESTful API server should be self-documented using OpenAPI (fka Swagger)
  specifications, so interactive documentation UI is in place;
* Authentication is handled with OAuth2 and using Resource Owner Password
  Credentials Grant (Password Flow) for first-party clients makes it usable
  not only for third-party "external" apps;
* Permissions are handled (and automaticaly documented);
* PATCH method can be handled accordingly to
  [RFC 6902](http://tools.ietf.org/html/rfc6902);
* Extensive testing with good code coverage.

I had to patch Flask-RESTplus (see `flask_restplus_patched` folder), so it can
handle Marshmallow schemas and Webargs arguments.

Here is how it looks at this point of time:

![Flask RESTplus Example API](https://raw.githubusercontent.com/frol/flask-restplus-server-example/master/docs/static/Flask_RESTplus_Example_API.png)


Project Structure
-----------------

### Root folder

Folders:

* `app` - This RESTful API Server example implementation is here.
* `flask_restplus_patched` - There are some patches for Flask-RESTPlus (read
  more in *Patched Dependencies* section).
* `migrations` - Database migrations are stored here (see `invoke --list` to
  learn available commands, and learn more about PyInvoke usage below).
* `tasks` - [PyInvoke](http://www.pyinvoke.org/) commands are implemented here.
* `tests` - These are [pytest](http://pytest.org) tests for this RESTful API
  Server example implementation.
* `docs` - It contains just images for the README, so you can safely ignore it.
* `deploy` - It contains some application stack examples.

Files:

* `README.md`
* `config.py` - This is a config file of this RESTful API Server example.
* `conftest.py` - A top-most pytest config file (it is empty, but it [helps to
  have a proper PYTHON PATH](http://stackoverflow.com/a/20972950/1178806)).
* `.coveragerc` - [Coverage.py](http://coverage.readthedocs.org/) (code
  coverage) config for code coverage reports.
* `.travis.yml` - [Travis CI](https://travis-ci.org/) (automated continuous
  integration) config for automated testing.
* `.pylintrc` - [Pylint](https://www.pylint.org/) config for code quality
  checking.
* `Dockerfile` - Docker config file which is used to build a Docker image
  running this RESTful API Server example.
* `.dockerignore` - Lists files and file masks of the files which should be
  ignored while Docker build process.
* `.gitignore` - Lists files and file masks of the files which should not be
  added to git repository.
* `LICENSE` - MIT License, i.e. you are free to do whatever is needed with the
  given code with no limits.

### Application Structure

```
app/
├── requirements.txt
├── __init__.py
├── extensions
│   └── __init__.py
└── modules
    ├── __init__.py
    ├── api
    │   └── __init__.py
    ├── auth
    │   ├── __init__.py
    │   ├── models.py
    │   ├── parameters.py
    │   └── views.py
    ├── users
    │   ├── __init__.py
    │   ├── models.py
    │   ├── parameters.py
    │   ├── permissions.py
    │   ├── resources.py
    │   └── schemas.py
    └── teams
        ├── __init__.py
        ├── models.py
        ├── parameters.py
        ├── resources.py
        └── schemas.py
```

* `app/requirements.txt` - The list of Python (PyPi) requirements.
* `app/__init__.py` - The entrypoint to this RESTful API Server example
  application (Flask application is created here).
* `app/extensions` - All extensions (e.g. SQLAlchemy, OAuth2) are initialized
  here and can be used in the application by importing as, for example,
  `from app.extensions import db`.
* `app/modules` - All endpoints are expected to be implemented here in logicaly
  separated modules. It is up to you how to draw the line to separate concerns
  (e.g. you can implement a monolith `blog` module, or split it into
  `topics`+`comments` modules).

### Module Structure

Once you added a module name into `config.ENABLED_MODULES`, it is required to
have `your_module.init_app(app, **kwargs)` function. Everything else is
completely optional. Thus, here is the required minimum:

```
your_module/
└── __init__.py
```

, where `__init__.py` will look like this:

```python
def init_app(app, **kwargs):
    pass
```

In this example, however, `init_app` imports `resources` and registeres `api`
(an instance of (patched) `flask_restplus.Namespace`). Learn more about the
"big picture" in the next section.


Where to start reading the code?
--------------------------------

The easiest way to start the application is by using PyInvoke command `app.run`
implemented in [`tasks/app/run.py`](tasks/app/run.py):

```
$ invoke app.run
```

The command creates an application by running
[`app/__init__.py:create_app()`](app/__init__.py) function, which in its turn:

1. loads an application config;
2. initializes extensions:
   [`app/extensions/__init__.py:init_app()`](app/extensions/__init__.py);
3. initializes modules:
   [`app/modules/__init__.py:init_app()`](app/modules/__init__.py).

Modules initialization calls `init_app()` in every enabled module
(listed in `config.ENABLED_MODULES`).

Let's take `teams` module as an example to look further.
[`app/modules/teams/__init__.py:init_app()`](app/modules/teams/__init__.py)
imports and registers `api` instance of (patched) `flask_restplus.Namespace`
from `.resources`. Flask-RESTPlus `Namespace` is designed to provide similar
functionality as Flask `Blueprint`.

[`api.route()`](app/modules/teams/resources.py) is used to bind a
resource (classes inherited from `flask_restplus.Resource`) to a specific
route.

Lastly, every `Resource` should have methods which are lowercased HTTP method
names (i.e. `.get()`, `.post()`, etc). This is where users' requests end up.


Dependencies
------------

### Project Dependencies

* [**Python**](https://www.python.org/) 2.7, 3.3+ / pypy2 (2.5.0)
* [**flask-restplus**](https://github.com/noirbizarre/flask-restplus) (+
  [*flask*](http://flask.pocoo.org/))
* [**sqlalchemy**](http://www.sqlalchemy.org/) (+
  [*flask-sqlalchemy*](http://flask-sqlalchemy.pocoo.org/)) - Database ORM.
* [**sqlalchemy-utils**](https://sqlalchemy-utils.rtdf.org/) - for nice
  custom fields (e.g., `PasswordField`).
* [**alembic**](https://alembic.rtdf.org/) - for DB migrations.
* [**marshmallow**](http://marshmallow.rtfd.org/) (+
  [*marshmallow-sqlalchemy*](http://marshmallow-sqlalchemy.rtfd.org/),
  [*flask-marshmallow*](http://flask-marshmallow.rtfd.org/)) - for
  schema definitions. (*supported by the patched Flask-RESTplus*)
* [**webargs**](http://webargs.rtfd.org/) - for parameters (input arguments).
  (*supported by the patched Flask-RESTplus*)
* [**apispec**](http://apispec.rtfd.org/) - for *marshmallow* and *webargs*
  introspection. (*integrated into the patched Flask-RESTplus*)
* [**oauthlib**](http://oauthlib.rtfd.org/) (+
  [*flask-oauthlib*](http://flask-oauthlib.rtfd.org/)) - for authentication.
* [**flask-login**](http://flask-login.rtfd.org/) - for `current_user`
  integration only.
* [**bcrypt**](https://github.com/pyca/bcrypt/) - for password hashing (used as
  a backend by *sqlalchemy-utils.PasswordField*).
* [**permission**](https://github.com/hustlzp/permission) - for authorization.
* [**Swagger-UI**](https://github.com/swagger-api/swagger-ui) - for interactive
  RESTful API documentation.

### Build Dependencies

I use [`pyinvoke`](http://pyinvoke.org) with custom tasks to maintain easy and
nice command-line interface. Thus, it is required to have `invoke` Python
package installed, and optionally you may want to install `colorlog`, so your
life become colorful.

### Patched Dependencies

* **flask-restplus** is patched to handle marshmallow schemas and webargs
  input parameters
  ([GH #9](https://github.com/noirbizarre/flask-restplus/issues/9)).
* **swagger-ui** (*the bundle is automatically downloaded on the first run*)
  just includes a pull-request to support Resource Owner Password Credentials
  Grant OAuth2 (aka Password Flow)
  ([PR #1853](https://github.com/swagger-api/swagger-ui/pull/1853)).


Installation
------------

### Using Docker

It is very easy to start exploring the example using Docker:

```bash
$ docker run -it --rm --publish 5000:5000 frolvlad/flask-restplus-server-example
```

[![](https://badge.imagelayers.io/frolvlad/flask-restplus-server-example:latest.svg)](https://imagelayers.io/?images=frolvlad/flask-restplus-server-example:latest 'Get your own badge on imagelayers.io')


### From sources

#### Clone the Project

```bash
$ git clone https://github.com/frol/flask-restplus-server-example.git
```

#### Setup Environment

It is recommended to use virtualenv or Anaconda/Miniconda to manage Python
dependencies. Please, learn details yourself.

You will need `invoke` package to work with everything related to this project.

```bash
$ pip install invoke colorlog
```


#### Run Server

NOTE: All dependencies and database migrations will be automatically handled,
so go ahead and turn the server ON! (Read more details on this in Tips section)

```bash
$ invoke app.run
```


Quickstart
----------

Open online interactive API documentation:
[http://127.0.0.1:5000/api/v1/](http://127.0.0.1:5000/api/v1/)

Autogenerated swagger config is always available from
[http://127.0.0.1:5000/api/v1/swagger.json](http://127.0.0.1:5000/api/v1/swagger.json)

`example.db` (SQLite) includes 2 users:

* Admin user `root` with password `q`
* Regular user `user` with password `w`

NOTE: Use On/Off switch in documentation to sign in.


Tips
----

Once you have invoke, you can learn all available commands related to this
project from:

```bash
$ invoke --list
```

Learn more about each command with the following syntax:

```bash
$ invoke --help <task>
```

For example:

```bash
$ invoke --help app.run
Usage: inv[oke] [--core-opts] app.run [--options] [other tasks here ...]

Docstring:
  Run DDOTS RESTful API Server.

Options:
  -d, --[no-]development
  -h STRING, --host=STRING
  -i, --[no-]install-dependencies
  -p, --port
  -u, --[no-]upgrade-db
```

Use the following command to enter ipython shell (`ipython` must be installed):

```bash
$ invoke app.env.enter
```

`app.run` and `app.env.enter` tasks automatically prepare all dependencies
(using `pip install`) and migrate database schema to the latest version.

Database schema migration is handled via `app.db.*` tasks group. The most
common migration commands are `app.db.upgrade` (it is automatically run on
`app.run`), and `app.db.migrate` (creates a new migration).


Useful Links
============

* "[The big Picture](https://identityserver.github.io/Documentation/docs/overview/bigPicture.html)" -
  short yet complete idea about how the modern apps should talk.
* "[Please. Don't PATCH Like An Idiot.](http://williamdurand.fr/2014/02/14/please-do-not-patch-like-an-idiot/)"
* "[Best Practices for Designing a Pragmatic RESTful API](http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api)"
* "[My take on RESTful authentication](https://facundoolano.wordpress.com/2013/12/23/my-take-on-restful-authentication/)"
