# github_api.py
from github import Github

class GitHubClient:
    def __init__(self, access_token):
        self.client = Github(access_token)

    def get_repositories(self, username):
        try:
            user = self.client.get_user(username)
            repos = user.get_repos()
            repo_data = []
            for repo in repos:
                repo_data.append({
                    'name': repo.name,
                    'url': repo.html_url,
                    'commits': self.get_commits(repo)
                })
            return repo_data
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_commits(self, repo):
        try:
            commits = repo.get_commits()
            commit_data = []
            for commit in commits[:5]:
                commit_data.append({
                    'message': commit.commit.message,
                    'url': commit.html_url
                })
            return commit_data
        except Exception as e:
            print(f"Error: {e}")
            return None

