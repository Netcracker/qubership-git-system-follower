# Registries
gsf tries to behave similarly to docker when working with docker images (and OCI artifacts): similar processing, defaults, etc.

!!! note
    This is done based on the oras python sdk, that is, all the specifications that [oras](https://oras.land) supports are supported by gsf

Supported specs:

1. [Docker Registry HTTP API v2](https://distribution.github.io/distribution/spec/api/) (with [Registry Authentication](https://docs.docker.com/reference/api/registry/auth/))
2. [OCI Distribution Specs](https://opencontainers.org/posts/blog/2024-03-13-image-and-distribution-1-1/)

## Specific registry authentication
Some registries, such as **AWS ECR**, introduce their own custom "enhancements" on top of the classic
Docker authentication mechanisms like **Basic** and **Bearer**. Any additional authentication logic is left to the user or the orchestration system in place.

For AWS ECR specifically, you can authenticate using the AWS CLI (after configuring your local AWS account) like so:
```bash
aws ecr get-authorization-token --output text --query 'authorizationData[].authorizationToken' | gsf install ...
```

!!! note
    AWS ECR does not use Bearer authentication. Instead, it relies on **Basic** authentication, 
    where the **username** is literally `AWS`, and the **password** is a temporary token (which lasts for 12 hours) obtained 
    via `aws ecr get-authorization-token`.