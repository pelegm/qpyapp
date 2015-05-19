"""
.. gitcomp.py

Git component for apps.
"""

## App Framework
import qpyapp.base

## Git framework
import git


_version_kwargs = dict(
    all=False, always=True, tags=True, long=True, abbrev=8, dirty="+"
)


class GitComp(qpyapp.base.Component):
    def __init__(self, app):
        ## Get git date
        self._init_git()

        ## Overload
        app_cls = type(app)
        app_cls.branch = property(lambda app: self.branch)
        app_cls.version = property(lambda app: self.version)

        ## Amend description
        try:
            self._orig_desc = app.description
        except AttributeError:
            pass
        else:
            app_cls.description = property(
                lambda app: "{} {}".format(self._orig_desc, self.version))

        ## Fetch git general data
        app.git_data = ""
        app.git_data += self._commit_sha + "\n\n"
        app.git_data += "Merged branches:\n"
        merged = list(self._merged_branches())
        for branch in merged:
            app.git_data += "  " + branch + "\n"
        diffs = self._diff
        if diffs:
            app.git_data += "\nDiffs:\n\n"
            app.git_data += ("="*72+"\n").join(diffs)

    def _init_git(self):
        self._repo = git.Repo()
        self._branch = self._repo.active_branch
        self.branch = self._branch.name
        self._git = self._repo.git
        self.version = self._git.describe(**_version_kwargs)
        self._commit = self._repo.commit()
        self._commit_sha = self._commit.hexsha
        self._diff = self._git.diff("HEAD")

    def _merged_branches(self):
        output = self._git.branch(merged=True)
        output_list = output.split("\n")

        branches = set()
        for line in output_list:
            if len(line) > 0:
                if output[0] == " " or output[0] == "*":
                    branches.add(output[2:])

        branches -= set([self.branch])
        return branches
