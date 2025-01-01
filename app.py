from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Daftar repository yang dimonitor
repositories = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add-repo', methods=['POST'])
def add_repo():
    data = request.json
    repo_url = data.get('repo_url')

    if not repo_url or "github.com" not in repo_url:
        return jsonify({"error": "Invalid GitHub repository URL"}), 400

    try:
        _, owner, repo = repo_url.rstrip('/').split('/')[-3:]
        repositories.append({"owner": owner, "repo": repo})
        return jsonify({"message": "Repository added successfully", "repositories": repositories})
    except ValueError:
        return jsonify({"error": "Invalid repository format"}), 400

@app.route('/commits', methods=['GET'])
def get_commits():
    """
    Mendapatkan daftar SHA commit dari repository.
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')

    if not owner or not repo:
        return jsonify({"error": "owner and repo are required"}), 400

    commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"

    try:
        response = requests.get(commits_url)
        response.raise_for_status()
        commits = response.json()

        # Format data commit
        commit_list = [
            {"sha": commit["sha"], "message": commit["commit"]["message"], "author": commit["commit"]["author"]["name"], "date": commit["commit"]["author"]["date"]}
            for commit in commits
        ]

        return jsonify(commit_list)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/commit-details', methods=['GET'])
def commit_details():
    """
    Mendapatkan detail commit berdasarkan SHA.
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')
    sha = request.args.get('sha')

    if not owner or not repo or not sha:
        return jsonify({"error": "owner, repo, and sha are required"}), 400

    commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"

    try:
        response = requests.get(commit_url)
        response.raise_for_status()
        commit_data = response.json()

        # Format data commit
        commit_details = {
            "sha": commit_data["sha"],
            "message": commit_data["commit"]["message"],
            "author": commit_data["commit"]["author"]["name"],
            "date": commit_data["commit"]["author"]["date"],
            "stats": commit_data.get("stats", {}),
            "files": [
                {
                    "filename": file["filename"],
                    "additions": file["additions"],
                    "deletions": file["deletions"],
                    "changes": file["changes"],
                    "status": file["status"]
                }
                for file in commit_data.get("files", [])
            ]
        }

        return jsonify(commit_details)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/all-commit-changes', methods=['GET'])
def all_commit_changes():
    """
    Hitung total perubahan dari semua commit di repository.
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')

    if not owner or not repo:
        return jsonify({"error": "owner and repo are required"}), 400

    commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    total_additions = 0
    total_deletions = 0
    total_changes = 0

    try:
        # Ambil daftar commit
        response = requests.get(commits_url)
        response.raise_for_status()
        commits = response.json()

        for commit in commits:
            sha = commit["sha"]
            commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"

            # Ambil detail setiap commit
            commit_response = requests.get(commit_url)
            commit_response.raise_for_status()
            commit_data = commit_response.json()

            stats = commit_data.get("stats", {})
            total_additions += stats.get("additions", 0)
            total_deletions += stats.get("deletions", 0)
            total_changes += stats.get("total", 0)

        return jsonify({
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_changes": total_changes
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
