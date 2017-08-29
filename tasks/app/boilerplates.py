# pylint: disable=line-too-long
"""
Boilerplates
"""
from __future__ import print_function

import logging
import os
import re

from jinja2 import Environment, FileSystemLoader

try:
    from invoke import ctask as task
except ImportError:  # Invoke 0.13 renamed ctask to task
    from invoke import task


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@task(default=True)
def crud_module(context, name='new_module', singular=None):
    """
    Create CRUD empty module with `name` (app.boilerplates.crud_module --name=articles --singular=article)
    """
    assert re.match('^[a-zA-Z0-9_]+$', name)

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
        log.critical('Module `%s` already exists.' % name)
        return

    os.makedirs(module_path)

    env = Environment(
        loader=FileSystemLoader('tasks/app/boilerplates_templates/crud_module')
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
