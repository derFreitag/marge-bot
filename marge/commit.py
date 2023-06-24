import re
import urllib.parse
from typing import TYPE_CHECKING, List

from . import gitlab

GET = gitlab.GET


class Commit(gitlab.Resource):
    @classmethod
    def fetch_by_id(cls, project_id: int, sha: str, api: gitlab.Api) -> "Commit":
        info = api.call(
            GET(
                f"/projects/{project_id}/repository/commits/{sha}",
            )
        )
        if TYPE_CHECKING:
            assert isinstance(info, dict)
        return cls(api, info)

    @classmethod
    def last_on_branch(cls, project_id: int, branch: str, api: gitlab.Api) -> "Commit":
        info = api.call(
            GET(
                f"/projects/{project_id}/repository/branches/"
                f'{urllib.parse.quote(branch, safe="")}',
            )
        )
        if TYPE_CHECKING:
            assert isinstance(info, dict)
        commit_info = info["commit"]
        return cls(api, commit_info)

    @property
    def id(self) -> str:
        result = self._info["id"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    @property
    def short_id(self) -> str:
        result = self.info["short_id"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    @property
    def title(self) -> str:
        result = self.info["title"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    @property
    def author_name(self) -> str:
        result = self.info["author_name"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    @property
    def author_email(self) -> str:
        result = self.info["author_email"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    @property
    def status(self) -> str:
        result = self.info["status"]
        if TYPE_CHECKING:
            assert isinstance(result, str)
        return result

    @property
    def reviewers(self) -> List[str]:
        return re.findall(
            r"^Reviewed-by: ([^\n]+)$", self.info["message"], re.MULTILINE
        )

    @property
    def testers(self) -> List[str]:
        return re.findall(r"^Tested-by: ([^\n]+)$", self.info["message"], re.MULTILINE)
