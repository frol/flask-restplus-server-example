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
