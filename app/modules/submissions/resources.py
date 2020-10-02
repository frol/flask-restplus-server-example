# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation
"""
RESTful API Submissions resources
--------------------------
"""

import logging
import os

from flask import request, current_app
from flask_login import current_user
from flask_restplus_patched import Resource
from flask_restplus._http import HTTPStatus

from app.extensions import db
from app.extensions.api import Namespace
from app.extensions.api.parameters import PaginationParameters
from app.modules.users import permissions


from . import parameters, schemas
from .models import Submission


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('submissions', description='Submissions')  # pylint: disable=invalid-name


@api.route('/')
@api.login_required(oauth_scopes=['submissions:read'])
class Submissions(Resource):
    """
    Manipulations with Submissions.
    """

    @api.parameters(PaginationParameters())
    @api.response(schemas.BaseSubmissionSchema(many=True))
    def get(self, args):
        """
        List of Submission.

        Returns a list of Submission starting from ``offset`` limited by ``limit``
        parameter.
        """
        return Submission.query.offset(args['offset']).limit(args['limit'])

    @api.login_required(oauth_scopes=['submissions:write'])
    @api.parameters(parameters.CreateSubmissionParameters())
    @api.response(schemas.DetailedSubmissionSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def post(self, args):
        """
        Create a new instance of Submission.
        """
        context = api.commit_or_abort(
            db.session, default_error_message='Failed to create a new Submission'
        )
        with context:
            args['owner_guid'] = current_user.guid
            submission = Submission(**args)
            db.session.add(submission)
        repo, project = submission.init_repository()
        log.info('Initialized LOCAL  Repo: %r' % (repo.working_tree_dir,))
        log.info('Initialized REMOTE Repo: %r' % (project.web_url,))
        return submission


@api.route('/streamlined')
@api.login_required(oauth_scopes=['submissions:write'])
class SubmissionsStreamlined(Resource):
    """
    Manipulations with Submissions + File add/commit.
    """

    @api.parameters(parameters.CreateSubmissionParameters())
    @api.response(schemas.DetailedSubmissionSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def post(self, args):
        """
        Create a new instance of Submission.
        """
        context = api.commit_or_abort(
            db.session, default_error_message='Failed to create a new Submission'
        )
        with context:
            args['owner_guid'] = current_user.guid
            submission = Submission(**args)
            db.session.add(submission)

        repo, project = submission.init_repository()

        log.info('Initialized LOCAL  Repo: %r' % (repo.working_tree_dir,))
        log.info('Initialized REMOTE Repo: %r' % (project.web_url,))

        for file in request.files.getlist('files'):
            file_repo_path = os.path.join(
                repo.working_tree_dir, '_submission', file.filename
            )
            file.save(file_repo_path)
            log.info('Wrote file and added to local repo: %r' % (file_repo_path,))

        repo.index.add('_assets/')
        repo.index.add('_submission/')
        repo.index.add('metadata.json')

        repo.index.commit('Initial commit via %s' % (request.url_rule,))

        # Get remote URL
        original_url = repo.remotes.origin.url

        # Update remote URL with PAT
        remote_personal_access_token = current_app.config.get(
            'GITLAB_REMOTE_LOGIN_PAT', None
        )
        push_url = original_url.replace(
            'https://', 'https://oauth2:%s@' % (remote_personal_access_token,)
        )
        repo.remotes.origin.set_url(push_url)

        # PUSH
        log.info('Pushing to authorized URL: %r' % (original_url,))
        repo.git.push('--set-upstream', repo.remotes.origin, repo.head.ref)
        log.info(
            '...pushed to %s' % (repo.head.ref),
        )

        # Reset URL on remote
        repo.remotes.origin.set_url(original_url)

        return submission


@api.route('/<uuid:submission_guid>')
@api.login_required(oauth_scopes=['submissions:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND,
    description='Submission not found.',
)
@api.resolve_object_by_model(Submission, 'submission')
class SubmissionByID(Resource):
    """
    Manipulations with a specific Submission.
    """

    @api.response(schemas.DetailedSubmissionSchema())
    def get(self, submission):
        """
        Get Submission details by ID.
        """
        return submission

    @api.login_required(oauth_scopes=['submissions:write'])
    @api.permission_required(permissions.WriteAccessPermission())
    @api.parameters(parameters.PatchSubmissionDetailsParameters())
    @api.response(schemas.DetailedSubmissionSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def patch(self, args, submission):
        """
        Patch Submission details by ID.
        """
        context = api.commit_or_abort(
            db.session, default_error_message='Failed to update Submission details.'
        )
        with context:
            parameters.PatchSubmissionDetailsParameters.perform_patch(
                args, obj=submission
            )
            db.session.merge(submission)
        return submission

    @api.login_required(oauth_scopes=['submissions:write'])
    @api.permission_required(permissions.WriteAccessPermission())
    @api.response(code=HTTPStatus.CONFLICT)
    @api.response(code=HTTPStatus.NO_CONTENT)
    def delete(self, submission):
        """
        Delete a Submission by ID.
        """
        context = api.commit_or_abort(
            db.session, default_error_message='Failed to delete the Submission.'
        )
        with context:
            db.session.delete(submission)
        return None
