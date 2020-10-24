# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import config
import shutil
import uuid
import os


def test_ensure_submission_by_uuid(
    flask_app_client, regular_user, db, test_submission_uuid
):
    # pylint: disable=invalid-name
    temp_submission = None

    try:
        from app.modules.submissions.models import Submission

        with flask_app_client.login(regular_user, auth_scopes=('submissions:read',)):
            response = flask_app_client.get(
                '/api/v1/submissions/%s' % test_submission_uuid
            )

        temp_submission = Submission.query.get(response.json['guid'])

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert isinstance(response.json, dict)
        assert set(response.json.keys()) >= {'guid', 'owner_guid', 'major_type', 'commit'}
        assert response.json.get('guid') == str(test_submission_uuid)
    except Exception as ex:
        raise ex
    finally:
        # Restore original state
        if temp_submission is not None:
            temp_submission.delete()


def test_ensure_empty_submission_by_uuid(
    flask_app_client, regular_user, db, test_empty_submission_uuid
):
    # pylint: disable=invalid-name
    temp_submission = None

    try:
        from app.modules.submissions.models import Submission

        with flask_app_client.login(regular_user, auth_scopes=('submissions:read',)):
            response = flask_app_client.get(
                '/api/v1/submissions/%s' % test_empty_submission_uuid
            )

        temp_submission = Submission.query.get(response.json['guid'])

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert isinstance(response.json, dict)
        assert set(response.json.keys()) >= {'guid', 'owner_guid', 'major_type', 'commit'}
        assert response.json.get('guid') == str(test_empty_submission_uuid)
    except Exception as ex:
        raise ex
    finally:
        # Restore original state
        if temp_submission is not None:
            temp_submission.delete()


def test_ensure_clone_submission_by_uuid(
    flask_app_client, regular_user, db, test_clone_submission_uuid
):
    # pylint: disable=invalid-name
    temp_submission = None

    submissions_database_path = config.TestingConfig.SUBMISSIONS_DATABASE_PATH
    submission_path = os.path.join(
        submissions_database_path, str(test_clone_submission_uuid)
    )

    if os.path.exists(submission_path):
        shutil.rmtree(submission_path)
    assert not os.path.exists(submission_path)

    try:
        from app.modules.submissions.models import Submission, SubmissionMajorType

        with flask_app_client.login(regular_user, auth_scopes=('submissions:read',)):
            response = flask_app_client.get(
                '/api/v1/submissions/%s' % test_clone_submission_uuid
            )

        temp_submission = Submission.query.get(response.json['guid'])

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert isinstance(response.json, dict)
        assert set(response.json.keys()) >= {'guid', 'owner_guid', 'major_type', 'commit'}
        assert response.json.get('guid') == str(test_clone_submission_uuid)

        assert temp_submission.major_type == SubmissionMajorType.test
        assert temp_submission.commit == 'e94db0cf015c6c84ab1668186924dc985fc472d6'
        assert temp_submission.commit_mime_whitelist_guid == uuid.UUID(
            '4d46c55d-accf-29f1-abe7-a24839ec1b95'
        )
        assert temp_submission.commit_houston_api_version == '0.1.0.8b208226'
        assert temp_submission.description == 'Test Submission (streamlined)'
    except Exception as ex:
        raise ex
    finally:
        # Restore original state
        if temp_submission is not None:
            temp_submission.delete()
        if os.path.exists(submission_path):
            shutil.rmtree(submission_path)
