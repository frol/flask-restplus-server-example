RESTful API Server Example deployments
======================================

This folder features a few deployment strategies for the [example RESTful API server](../api/).

Index
-----

* `stack1` - RESTful API Server Example behind an nginx reverse proxy, stack
managed using Docker Compose.
* `stack2` - stack1 running on uWSGI instead of the default Flask server.

Tips
----

* It is advisable to run web services over HTTPS instead of HTTP. Take a look at
  [Let's Encrypt](https://letsencrypt.org/) if you don't want to pay money for
  SSL certificates.
* It makes a lot of sense to use a reliable Reverse Proxy server in front of
  Flask (or any other framework, in fact). My choice is Nginx.
* Using a Reverse Proxy, you should enable `REVERSE_PROXY_SETUP` in the config
  or pass `EXAMPLE_API_REVERSE_PROXY_SETUP=1` via environment variables (the
  showcased stacks do that, so you don't need to do that if you follow the
  guide), so special proxyfied headers (`X-Forwarded-Proto`, and others) are
  taken into account.
