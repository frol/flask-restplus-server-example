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
        from app.modules.assets.models import Asset

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

        # Checks that there are two valid Assets in the database
        assert len(temp_submission.assets) == 2
        temp_assets = sorted(temp_submission.assets)
        expected_guid_list = [
            uuid.UUID('3abc03a8-39c8-42c4-bedb-e08ccc485396'),
            uuid.UUID('aee00c38-137e-4392-a4d9-92b545a9efb0'),
        ]
        for asset, expected_guid in zip(temp_assets, expected_guid_list):
            db_asset = Asset.query.get(asset.guid)
            assert asset == db_asset
            assert asset.guid == expected_guid

    except Exception as ex:
        raise ex
    finally:
        # Restore original state
        if temp_submission is not None:
            temp_submission.delete()
        if os.path.exists(submission_path):
            shutil.rmtree(submission_path)
