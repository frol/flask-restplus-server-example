# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import json
import filecmp
import config
from os.path import join, basename


def test_create_open_submission(flask_app_client, regular_user, db):
    # pylint: disable=invalid-name
    try:

        from app.modules.submissions.models import Submission, SubmissionMajorType

        test_major_type = SubmissionMajorType.test

        with flask_app_client.login(regular_user, auth_scopes=('submissions:write',)):
            response = flask_app_client.post(
                '/api/v1/submissions/',
                data=json.dumps(
                    {
                        'major_type': test_major_type,
                        'title': 'Test Submission',
                        'description': 'This is a test submission, please ignore',
                    }
                ),
            )

        temp_submission = Submission.query.get(response.json['guid'])

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert isinstance(response.json, dict)
        assert set(response.json.keys()) >= {
            'guid',
            'commit',
            'major_type',
            'owner_guid',
        }

        assert temp_submission.commit is None
        assert temp_submission.major_type == test_major_type
    except Exception as ex:
        raise ex
    finally:
        # Restore original state
        with db.session.begin():
            db.session.delete(temp_submission)


def test_submission_streamlined(flask_app_client, regular_user, db):
    # pylint: disable=invalid-name
    try:

        from app.modules.submissions.models import Submission, SubmissionMajorType

        test_major_type = SubmissionMajorType.test
        test_root = join(
            config.TestingConfig.PROJECT_ROOT, 'tests', 'submissions', 'test-000'
        )
        test_image_list = ['zebra.jpg', 'fluke.jpg']
        files = [
            _upload_content(join(test_root, filename)) for filename in test_image_list
        ]

        with flask_app_client.login(regular_user, auth_scopes=('submissions:write',)):
            response = flask_app_client.post(
                '/api/v1/submissions/streamlined',
                data=dict(
                    major_type=test_major_type,
                    title='Test Submission',
                    description='Test Submission (streamlined)',
                    files=files,
                ),
            )
        # since we passed file descriptors to files we need to close them now
        [f[0].close() for f in files]

        temp_submission = Submission.query.get(response.json['guid'])

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert isinstance(response.json, dict)
        assert set(response.json.keys()) >= {
            'guid',
            'commit',
            'major_type',
            'owner_guid',
        }

        # is this the right way to get (local) repo ??
        repo, project = temp_submission.init_repository()

        # ### compares file in local repo
        for filename in test_image_list:
            local_filepath = join(test_root, filename)
            repo_filepath = join(repo.working_tree_dir, '_submission', filename)
            assert filecmp.cmp(local_filepath, repo_filepath)
        # ## TODO other tests?  confirm commit, confirm remote has files, etc?????  (once i get push working!)

        assert temp_submission.commit is None
        assert temp_submission.major_type == test_major_type
    except Exception as ex:
        raise ex
    finally:
        # Restore original state
        with db.session.begin():
            db.session.delete(temp_submission)


def _upload_content(path):
    bname = basename(path)
    return open(path, 'rb'), bname
