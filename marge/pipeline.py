from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from . import gitlab

GET, POST = gitlab.GET, gitlab.POST


class Pipeline(gitlab.Resource):
    def __init__(self, api: gitlab.Api, info: Dict[str, Any], project_id: int):
        info["project_id"] = project_id
        super().__init__(api, info)

    @classmethod
    def pipelines_by_branch(
        cls,
        project_id: int,
        branch: str,
        api: gitlab.Api,
        *,
        ref: Optional[str] = None,
        status: Optional[str] = None,
        order_by: str = "id",
        sort: str = "desc",
    ) -> List["Pipeline"]:
        params = {
            "ref": branch if ref is None else ref,
            "order_by": order_by,
            "sort": sort,
        }
        if status is not None:
            params["status"] = status
        pipelines_info = api.call(
            GET(
                f"/projects/{project_id}/pipelines",
                params,
            )
        )
        if TYPE_CHECKING:
            assert isinstance(pipelines_info, list)

        return [cls(api, pipeline_info, project_id) for pipeline_info in pipelines_info]

    @classmethod
    def pipelines_by_merge_request(
        cls, project_id: int, merge_request_iid: int, api: gitlab.Api
    ) -> List["Pipeline"]:
        """Fetch all pipelines for a merge request in descending order of
        pipeline ID."""
        pipelines_info = api.call(
            GET(f"/projects/{project_id}/merge_requests/{merge_request_iid}/pipelines")
        )
        if TYPE_CHECKING:
            assert isinstance(pipelines_info, list)
        pipelines_info.sort(
            key=lambda pipeline_info: cast(str, pipeline_info["id"]), reverse=True
        )
        return [cls(api, pipeline_info, project_id) for pipeline_info in pipelines_info]

    @property
    def project_id(self) -> int:
        result = self.info["project_id"]
        if TYPE_CHECKING:
            assert isinstance(result, int)
        return result

    @property
    def id(self) -> int:
        result = self.info["id"]
        if TYPE_CHECKING:
            assert isinstance(result, int)
        return result

    @property
    def status(self) -> str:
        result = self.info["status"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    @property
    def ref(self) -> str:
        result = self.info["ref"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    @property
    def sha(self) -> str:
        result = self.info["sha"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    @property
    def web_url(self) -> str:
        result = self.info["web_url"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    def cancel(self) -> Dict[str, Any]:
        result = self._api.call(
            POST(
                f"/projects/{self.project_id}/pipelines/{self.id}/cancel",
            )
        )
        if TYPE_CHECKING:
            assert isinstance(result, dict)
        return result
