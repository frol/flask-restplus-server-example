# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring


def test_ensure_submission_by_uuid(
    flask_app_client, regular_user, db, test_submission_uuid
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('submissions:read',)):
        response = flask_app_client.get('/api/v1/submissions/%s' % test_submission_uuid)

    assert response.status_code == 403
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'status', 'message'}
