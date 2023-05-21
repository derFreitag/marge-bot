from . import gitlab

GET = gitlab.GET


class Branch(gitlab.Resource):
    @classmethod
    def fetch_by_name(cls, project_id, branch, api) -> "Branch":
        info = api.call(
            GET(
                f"/projects/{project_id}/repository/branches/{branch}",
            )
        )
        return cls(api, info)

    @property
    def name(self):
        return self.info["name"]

    @property
    def protected(self):
        return self.info["protected"]
