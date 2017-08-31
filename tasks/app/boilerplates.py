# pylint: disable=line-too-long
"""
Boilerplates
"""
from __future__ import print_function

import logging
import os
import re

try:
    from invoke import ctask as task
except ImportError:  # Invoke 0.13 renamed ctask to task
    from invoke import task


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@task
def crud_module(context, name='', singular=''):
    # pylint: disable=unused-argument
    """
    Create CRUD (Create-Read-Update-Delete) empty module.

    Usage:
    $ invoke app.boilerplates.crud-module --name=articles --singular=article
    """
    try:
        import jinja2
    except ImportError:
        log.critical("jinja2 is required to create boilerplates. Please, do `pip install jinja2`")
        return

    if not name:
        log.critical("Module name is required")
        return

    if not re.match('^[a-zA-Z0-9_]+$', name):
        log.critical(
            "Module name is allowed to contain only letters, numbers and underscores "
            "([a-zA-Z0-9_]+)"
        )
        return

    if not singular:
        singular = name[:-1]

    module_path = 'app/modules/%s' % name

    module_title = " ".join(
        [word.capitalize()
            for word in name.split('_')
        ]
    )

    model_name = "".join(
        [word.capitalize()
            for word in singular.split('_')
        ]
    )

    if os.path.exists(module_path):
        log.critical('Module `%s` already exists.', name)
        return

    os.makedirs(module_path)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('tasks/app/boilerplates_templates/crud_module')
    )
    for template_file in (
        '__init__',
        'models',
        'parameters',
        'resources',
        'schemas',
    ):
        template = env.get_template('%s.py.template' % template_file)
        template.stream(
            module_title=module_title,
            model_name=model_name,
            module_name=name,
            module_name_singular=singular if singular else name
        ).dump(
            '%s/%s.py' % (module_path, template_file)
        )

    log.info("Module `%s` has been created.", name)
    print(
        "Add `%(module_name)s` to `ENABLED_MODULES` in `config.py`\n"
        "ENABLED_MODULES = (\n"
        "\t'auth',\n"
        "\t'users',\n"
        "\t'teams',\n"
        "\t'%(module_name)s',\n\n"
        "\t'api',\n"
        ")\n\n"
        "You can find your module at `app/modules/` directory"
        % {'module_name': name}
    )
