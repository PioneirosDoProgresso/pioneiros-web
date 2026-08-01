#!/usr/bin/env bash

set -euo pipefail

readonly REMOTE_NAME="origin"

require_git_repo() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "This script must run inside a Git repository." >&2
    exit 1
  fi
}

get_current_branch() {
  local branch_name

  branch_name="$(git rev-parse --abbrev-ref HEAD)"
  if [[ "${branch_name}" == "HEAD" ]]; then
    echo "Detached HEAD is not supported. Checkout a branch first." >&2
    exit 1
  fi

  printf '%s\n' "${branch_name}"
}

get_ssh_remote_url() {
  local remote_url

  remote_url="$(git remote get-url "${REMOTE_NAME}")"
  if [[ "${remote_url}" =~ ^git@github\.com:.+\.git$ ]]; then
    printf '%s\n' "${remote_url}"
    return 0
  fi

  if [[ "${remote_url}" =~ ^https://github\.com/(.+)\.git$ ]]; then
    printf 'git@github.com:%s.git\n' "${BASH_REMATCH[1]}"
    return 0
  fi

  echo "Unsupported remote URL for SSH push: ${remote_url}" >&2
  exit 1
}

main() {
  local branch_name
  local ssh_remote_url

  require_git_repo

  branch_name="$(get_current_branch)"
  ssh_remote_url="$(get_ssh_remote_url)"

  echo "Pushing ${branch_name} to ${ssh_remote_url}"
  git push "${ssh_remote_url}" "HEAD:refs/heads/${branch_name}"

  echo "Refreshing ${REMOTE_NAME}/${branch_name}"
  git fetch "${REMOTE_NAME}" "${branch_name}"

  echo "Push completed successfully."
}

main "$@"
