# Build Gear
Information on how to build your project as git-system-follower Gear


## OCI artifact
Recommended option when you build your Gear as an OCI artifact

Package file structure:
```plaintext
<your repository>
├─ git-system-follower-package/
│  └─ <package files>
└─ <your other files>
```

Command to publish your Gear:
```bash
oras push <your registry> git-system-follower-package/
```

## Docker image with artifact
Package file structure:
```plaintext
<your repository>
├─ git-system-follower-package/
│  └─ <package files>
├─ Dockerfile
└─ <your other files>
```

## `Dockerfile` file
This simply requires you to put the gear in the image
```Dockerfile
FROM scratch

LABEL gsf.package="true"

COPY git-system-follower-package /git-system-follower-package
```

Command to build & publish your Gear:
```bash
docker build -t <image>:<tag> .
docker push <registry>/<image>:<tag>
```