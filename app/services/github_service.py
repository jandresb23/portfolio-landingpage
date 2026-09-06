import httpx
from app.config import settings

# FIX ROBUSTEZ: sin timeout, una llamada colgada a GitHub bloquearía el
# endpoint /sync indefinidamente.
REQUEST_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class GitHubProvider:
    BASE_URL = "https://api.github.com"

    async def fetch_user_repositories(self) -> list:
        headers = {
            "Accept": "application/vnd.github+json",
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        url = f"{self.BASE_URL}/users/{settings.GITHUB_USERNAME}/repos?sort=updated&per_page=6"

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Error fetching GitHub repos: {response.text}")

            repos = response.json()
            formatted_repos = []
            for repo in repos:
                formatted_repos.append({
                    "repo_name": repo.get("name"),
                    "description": repo.get("description") or "Sin descripción disponible.",
                    "html_url": repo.get("html_url"),
                    "language": repo.get("language") or "General",
                    "updated_at": repo.get("updated_at")
                })
            return formatted_repos
