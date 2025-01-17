from unittest.mock import Mock, call

import pytest

import marge.user
from marge.gitlab import GET, POST, PUT, Api, BadRequest, Version
from marge.merge_request import NO_JOBS_MESSAGE, MergeRequest, MergeRequestRebaseFailed
from tests.test_user import INFO as USER_INFO

_MARGE_ID = 77

INFO = {
    "id": 42,
    "iid": 54,
    "title": "a title",
    "project_id": 1234,
    "assignees": [{"id": _MARGE_ID}],
    "author": {"id": 88},
    "state": "opened",
    "sha": "dead4g00d",
    "source_project_id": 5678,
    "target_project_id": 1234,
    "source_branch": "useless_new_feature",
    "force_remove_source_branch": True,
    "target_branch": "master",
    "draft": False,
}

DISCUSSION = {
    "id": "aabbcc0044",
    "notes": [
        {
            "id": 12,
            "body": "assigned to @john_smith",
            "created_at": "2020-08-04T06:56:11.854Z",
        },
        {
            "id": 13,
            "body": "assigned to @john_smith",
            "created_at": "2020-08-18T06:52:58.093Z",
        },
    ],
}


# pylint: disable=attribute-defined-outside-init
class TestMergeRequest:
    def setup_method(self, _method):
        self.api = Mock(Api)
        self.api.version = Mock(return_value=Version.parse("9.2.3-ee"))
        self.merge_request = MergeRequest(api=self.api, info=INFO)

    def test_fetch_by_iid(self):
        api = self.api
        api.call = Mock(return_value=INFO)

        merge_request = MergeRequest.fetch_by_iid(
            project_id=1234, merge_request_iid=54, api=api
        )

        api.call.assert_called_once_with(
            GET(
                "/projects/1234/merge_requests/54",
                {"include_rebase_in_progress": "true"},
            )
        )
        assert merge_request.info == INFO

    def test_refetch_info(self):
        new_info = dict(INFO, state="closed")
        self.api.call = Mock(return_value=new_info)

        self.merge_request.refetch_info()
        self.api.call.assert_called_once_with(
            GET(
                "/projects/1234/merge_requests/54",
                {"include_rebase_in_progress": "true"},
            )
        )
        assert self.merge_request.info == new_info

    def test_properties(self):
        assert self.merge_request.id == 42
        assert self.merge_request.project_id == 1234
        assert self.merge_request.iid == 54
        assert self.merge_request.title == "a title"
        assert self.merge_request.assignee_ids == [77]
        assert self.merge_request.author_id == 88
        assert self.merge_request.state == "opened"
        assert self.merge_request.source_branch == "useless_new_feature"
        assert self.merge_request.target_branch == "master"
        assert self.merge_request.sha == "dead4g00d"
        assert self.merge_request.source_project_id == 5678
        assert self.merge_request.target_project_id == 1234
        assert self.merge_request.draft is False

        self._load({"assignees": []})
        assert self.merge_request.assignee_ids == []

    def test_comment(self):
        self.merge_request.comment("blah")
        self.api.call.assert_called_once_with(
            POST(
                "/projects/1234/merge_requests/54/notes",
                {"body": "blah"},
            ),
        )

    def test_assign(self):
        self.merge_request.assign_to(42)
        self.api.call.assert_called_once_with(
            PUT("/projects/1234/merge_requests/54", {"assignee_id": 42})
        )

    def test_unassign(self):
        self.merge_request.unassign()
        self.api.call.assert_called_once_with(
            PUT("/projects/1234/merge_requests/54", {"assignee_id": 0})
        )

    def test_rebase_was_not_in_progress_no_error(self):
        expected = [
            (
                GET(
                    "/projects/1234/merge_requests/54",
                    {"include_rebase_in_progress": "true"},
                ),  # refetch_info -> not in progress
                INFO,
            ),
            (
                PUT("/projects/1234/merge_requests/54/rebase"),
                True,
            ),
            (
                GET(
                    "/projects/1234/merge_requests/54",
                    {"include_rebase_in_progress": "true"},
                ),  # refetch_info -> in progress
                dict(INFO, rebase_in_progress=True),
            ),
            (
                GET(
                    "/projects/1234/merge_requests/54",
                    {"include_rebase_in_progress": "true"},
                ),  # refetch_info -> succeeded
                dict(INFO, rebase_in_progress=False),
            ),
        ]

        self.api.call = Mock(side_effect=[resp for (req, resp) in expected])
        self.merge_request.rebase()
        self.api.call.assert_has_calls([call(req) for (req, resp) in expected])

    def test_rebase_was_not_in_progress_error(self):
        expected = [
            (
                GET(
                    "/projects/1234/merge_requests/54",
                    {"include_rebase_in_progress": "true"},
                ),  # refetch_info -> not in progress
                INFO,
            ),
            (
                PUT("/projects/1234/merge_requests/54/rebase"),
                True,
            ),
            (
                GET(
                    "/projects/1234/merge_requests/54",
                    {"include_rebase_in_progress": "true"},
                ),  # refetch_info -> BOOM
                dict(
                    INFO,
                    rebase_in_progress=False,
                    merge_error="Rebase failed. Please rebase locally",
                ),
            ),
        ]

        self.api.call = Mock(side_effect=[resp for (req, resp) in expected])

        with pytest.raises(MergeRequestRebaseFailed):
            self.merge_request.rebase()
        self.api.call.assert_has_calls([call(req) for (req, resp) in expected])

    def test_rebase_was_in_progress_no_error(self):
        expected = [
            (
                GET(
                    "/projects/1234/merge_requests/54",
                    {"include_rebase_in_progress": "true"},
                ),  # refetch_info -> in progress
                dict(INFO, rebase_in_progress=True),
            ),
            (
                GET(
                    "/projects/1234/merge_requests/54",
                    {"include_rebase_in_progress": "true"},
                ),  # refetch_info -> in progress
                dict(INFO, rebase_in_progress=True),
            ),
            (
                GET(
                    "/projects/1234/merge_requests/54",
                    {"include_rebase_in_progress": "true"},
                ),  # refetch_info -> succeeded
                dict(INFO, rebase_in_progress=False),
            ),
        ]
        self.api.call = Mock(side_effect=[resp for (req, resp) in expected])
        self.merge_request.rebase()
        self.api.call.assert_has_calls([call(req) for (req, resp) in expected])

    def test_accept_remove_branch(self):
        self._load(dict(INFO, sha="badc0de"))

        for boolean in (True, False):
            self.merge_request.accept(remove_branch=boolean)
            self.api.call.assert_called_once_with(
                PUT(
                    "/projects/1234/merge_requests/54/merge",
                    {
                        "merge_when_pipeline_succeeds": True,
                        "should_remove_source_branch": boolean,
                        "sha": "badc0de",
                    },
                )
            )
            self.api.call.reset_mock()

    def test_accept_sha(self):
        self._load(dict(INFO, sha="badc0de"))
        self.merge_request.accept(sha="g00dc0de")
        self.api.call.assert_called_once_with(
            PUT(
                "/projects/1234/merge_requests/54/merge",
                {
                    "merge_when_pipeline_succeeds": True,
                    "should_remove_source_branch": False,
                    "sha": "g00dc0de",
                },
            )
        )

    def test_accept_merge_when_pipeline_succeeds(self):
        self._load(dict(INFO, sha="badc0de"))
        self.merge_request.accept(merge_when_pipeline_succeeds=False)
        self.api.call.assert_called_once_with(
            PUT(
                "/projects/1234/merge_requests/54/merge",
                {
                    "merge_when_pipeline_succeeds": False,
                    "should_remove_source_branch": False,
                    "sha": "badc0de",
                },
            )
        )

    def test_fetch_all_opened_for_me(self):
        api = self.api
        mr1, mr_not_me, mr2 = (
            INFO,
            dict(INFO, assignees=[{"id": _MARGE_ID + 1}], id=679),
            dict(INFO, id=678),
        )
        user = marge.user.User(api=None, info=dict(USER_INFO, id=_MARGE_ID))
        api.collect_all_pages = Mock(return_value=[mr1, mr_not_me, mr2])
        result = MergeRequest.fetch_all_open_for_user(
            1234, user=user, api=api, merge_order="created_at"
        )
        api.collect_all_pages.assert_called_once_with(
            GET(
                "/projects/1234/merge_requests",
                {"state": "opened", "order_by": "created_at", "sort": "asc"},
            )
        )
        assert [mr.info for mr in result] == [mr1, mr2]

    def test_fetch_assigned_at(self):
        api = self.api
        dis1, dis2 = DISCUSSION, dict(DISCUSSION, id=679)
        mr1 = INFO
        user = marge.user.User(api=None, info=dict(USER_INFO, id=_MARGE_ID))
        api.collect_all_pages = Mock(return_value=[dis1, dis2])
        result = MergeRequest.fetch_assigned_at(user=user, api=api, merge_request=mr1)
        api.collect_all_pages.assert_called_once_with(
            GET(
                "/projects/1234/merge_requests/54/discussions",
            )
        )
        assert result == 1597733578.093

    def test_trigger_pipeline_succeeds(self):
        api = self.api
        expected_result = object()

        def side_effect(request):
            if request.endpoint == "/projects/1234/merge_requests/54/pipelines":
                return expected_result
            return None

        api.call = Mock(side_effect=side_effect)

        result = self.merge_request.trigger_pipeline()

        assert api.call.call_args_list == [
            call(POST("/projects/1234/merge_requests/54/pipelines")),
        ]

        assert result == expected_result

    def test_trigger_pipeline_fallback_succeeds(self):
        api = self.api
        expected_result = object()

        def side_effect(request):
            if request.endpoint == "/projects/1234/merge_requests/54/pipelines":
                raise BadRequest(400, {"message": NO_JOBS_MESSAGE})
            if request.endpoint == "/projects/1234/pipeline?ref=useless_new_feature":
                return expected_result
            return None

        api.call = Mock(side_effect=side_effect)

        result = self.merge_request.trigger_pipeline()

        assert api.call.call_args_list == [
            call(POST("/projects/1234/merge_requests/54/pipelines")),
            call(POST("/projects/1234/pipeline?ref=useless_new_feature")),
        ]

        assert result == expected_result

    def test_trigger_pipeline_fallback_fails(self):
        api = self.api

        def side_effect(request):
            if request.endpoint == "/projects/1234/merge_requests/54/pipelines":
                raise BadRequest(500, {"message": "Another error."})

        api.call = Mock(side_effect=side_effect)

        with pytest.raises(BadRequest):
            self.merge_request.trigger_pipeline()

        assert api.call.call_args_list == [
            call(POST("/projects/1234/merge_requests/54/pipelines")),
        ]

    def _load(self, json):
        old_mock = self.api.call
        self.api.call = Mock(return_value=json)
        self.merge_request.refetch_info()
        self.api.call.assert_called_with(
            GET(
                "/projects/1234/merge_requests/54",
                {"include_rebase_in_progress": "true"},
            )
        )
        self.api.call = old_mock
