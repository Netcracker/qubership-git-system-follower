# Component Release

This page describes how git-system-follower handles release tags for component gears.

## Overview

When a component gear (type: `component`) is installed, git-system-follower merges a merge request with the gear changes, creates a tag, and waits for the pipeline to complete.

git-system-follower creates the tag before the pipeline is triggered so the pipeline runs on a specific tag ref. The tag name is derived from the `version` field in the gear's `package.yaml`. This keeps a clean flow: merge → tag → pipeline.

## Gear developer setup

Gear developers should configure the gear's `.gitlab-ci.yml` to create a GitLab Release using the `release` keyword.

!!! important
    The pipeline runs on the **tag ref**, not the branch ref. Your pipeline triggers must use tag-based rules (e.g., `rules: - if: $CI_COMMIT_TAG`), not branch-based rules.

## Example GitLab CI configuration

```yaml
stages:
  - release

release:
  stage: release
  rules:
    - if: $CI_COMMIT_TAG
  script:
    - echo "Creating release for $CI_COMMIT_TAG"
  release:
    tag_name: $CI_COMMIT_TAG
    name: "Release $CI_COMMIT_TAG"
    description: "Release $CI_COMMIT_TAG created by git-system-follower"
```

## Rollback

When rolling back a component gear, git-system-follower deletes the tag if the target branch no longer has the component gear installed. This removes the associated GitLab Release.

## Error handling

- If the pipeline fails, git-system-follower exits with an error (exit code 1)
