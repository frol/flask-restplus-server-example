# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import json
import io
import os
import filecmp


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

        with flask_app_client.login(regular_user, auth_scopes=('submissions:write',)):
            response = flask_app_client.post(
                '/api/v1/submissions/streamlined',
                data=dict(
                    major_type=test_major_type,
                    title='Test Submission',
                    description='Test Submission (streamlined)',
                    files=[
                        (open('tests/submissions/test-000/fluke.jpg', 'rb'), 'fluke.jpg'),
                        (open('tests/submissions/test-000/zebra.jpg', 'rb'), 'zebra.jpg'),  #FIXME unclosed file warning
                    ]
                )
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

        repo, project = temp_submission.init_repository()   #is this the right way to get (local) repo ??
        #### compares file in local repo
        assert filecmp.cmp(repo.working_tree_dir + '/fluke.jpg', 'tests/submissions/test-000/fluke.jpg')
        assert filecmp.cmp(repo.working_tree_dir + '/zebra.jpg', 'tests/submissions/test-000/zebra.jpg')
        ### TODO other tests?  confirm commit, confirm remote has files, etc?????  (once i get push working!)

        assert temp_submission.commit is None
        assert temp_submission.major_type == test_major_type
    except Exception as ex:
        raise ex
    finally:
        # Restore original state
        with db.session.begin():
            db.session.delete(temp_submission)

