"""
Swagger related invoke tasks
"""
from __future__ import print_function

import logging
import os

try:
    from invoke import ctask as task
except ImportError:  # Invoke 0.13 renamed ctask to task
    from invoke import task


@task(default=True)
def export(context, output_format='json', quiet=False):
    """
    Export swagger.json content
    """
    # set logging level to ERROR to avoid [INFO] messages in result
    logging.getLogger().setLevel(logging.ERROR)

    from app import create_app
    app = create_app(flask_config_name='testing')
    swagger_content = app.test_client().get('/api/v1/swagger.%s' % output_format).data
    if not quiet:
        print(swagger_content.decode('utf-8'))
    return swagger_content


@task
def codegen(context, language, version, dry_run=False, offline=False):
    if dry_run:
        run = print
    else:
        run = context.run

    swagger_json_content = export(context, output_format='json', quiet=True)
    if dry_run:
        run(
            "cat >./clients/%(language)s/swagger.json <<'EOF'\n%(swagger_json_content)s\nEOF"
            % {
                'language': language,
                'swagger_json_content': swagger_json_content.decode('utf-8'),
            }
        )
    else:
        with open(os.path.join('.', 'clients', language, 'swagger.json'), 'wb') as swagger_json:
            swagger_json.write(swagger_json_content)

    if not offline:
        run(
            "docker pull 'khorolets/swagger-codegen'"
        )

    run(
        "cd './clients/%(language)s' ;"
        # Tar the config files to pass them into swagger-codegen docker-container.
        "tar -c swagger.json swagger_codegen_config.json"
        "  | docker run --interactive --rm --entrypoint /bin/sh 'khorolets/swagger-codegen' -c \""
        # Unpack them, generate library code with these files.
        "      tar -x ;"
        "      java -jar '/opt/swagger-codegen/modules/swagger-codegen-cli/target/swagger-codegen-cli.jar'"
        "        generate"
        "          --input-spec './swagger.json'"
        "          --lang '%(language)s'"
        "          --output './dist'"
        "          --config './swagger_codegen_config.json'"
        "          --additional-properties 'packageVersion=%(version)s,projectVersion=%(version)s'"
        "          >&2 ;"
        # tar the generated code and return it.
        "      tar -c dist\""
        # Finally, untar library source into current directory.
        "  | tar -x"
        % {
            'language': language,
            'version': version,
        }
    )
