# PitStop Deployment

A mini word vomit documenting my deployment process. Deployed on an old server running Docker VM with Portainer. Connections handled using Cloudflare Tunnel.

## Database

Somewhat straightforward, just needed to use a PostGIS base image to simplify subsequent initialization. Initially, the backend kept throwing errors as it was unable to connect to the database. Turns out that I forgot to create the init scripts to initialize the database and create the necessary tables in the volume. Those init scripts should run once on volume creation. Subsequent runs should not need initialization since the database is already present.

Portainer was unable to find the initialization scripts as I had used relative paths in the database bind mount. Hence, I created a separate directory and Dockerfile for the database service.

## Backend

By far the most complicated.

### Fetching and Loading Data into Database

Since fetching and loading the parking spots data was done using Python scripts, I needed to run them in the backend container. This also meant that the backend container depends on the database container to be up and running (and initialized) first, otherwise the scripts would throw errors.

The fetching script takes roughly 15-20s to run, which would be enough time for the database container to be started and initialized. However, a sanity check using `netcat` was done to ensure that the loading script only runs when a valid connection to the database container exists.

### Base Image and NumPy Issues

I used `python:3.12-slim` at first since Google said it provided faster download times and a reduced attack surface due to its smaller size. Building and running the services locally also worked flawlessly.

However, when deploying to the server, the backend container ended up throwing the most unexpected of errors. There was a runtime error when importing NumPy due to unsupported optimizations (might be due to the old age of the server). Regardless, I took the following steps to fix:

1. Downgrade NumPy from v2 to v1 — It made sense because v2 likely introduced new features that my old server cannot handle. But downgrading alone did not fix the issue.

2. Replace `slim` base image with `bookworm` — There might have been missing dependencies that the `slim` image had omitted. Not entirely sure what dependencies exactly, but replacing the base image solved the issue.

Then, I tried to upgrade NumPy back to v2 while still using `bookworm`. Alas, it broke again... Functionally, the app seemed to be unaffected even with NumPy v1; the route was still correctly being sliced into multiple segments.

### Cron Scheduling

This did not work. The idea was to schedule a cron job within the backend container that runs monthly to fetch and load the updated parking spots data (e.g., parking spots at newly-built estates). This way, PitStop's database of parking spots remains up-to-date over time. However, each Docker container should only run a single process in the foreground (i.e., the FastAPI server in the backend container).

Maybe I can spin up a separate service solely for running cron jobs... Until then, the parking spots data would have to be manually updated.

> Edit: Parking spots are now updated monthly using APScheduler inside the FastAPI server directly (i.e., instead of running the update scripts externally, it now runs as part of the server).

## Frontend

Straightforward. Used a Node base image and followed some articles online for writing the Dockerfile [[1](https://medium.com/@itsuki.enjoy/dockerize-a-next-js-app-4b03021e084d)]. Had to reconfigure 2 things:

1. `start` script in `[package.json](./frontend/package.json)` — Added host `0.0.0.0` and port `3000` parameters to ensure that the frontend is accessible (`0.0.0.0` for binding to all available IPv4 interfaces, `3000` is the exposed port as defined in the Dockerfile).

2. Rewrites in `[next.config.ts](./frontend/next.config.ts)` — Since I set up nginx to route requests to both the frontend and backend, there is no need for the rewrites configuration in the production environment (i.e., where the Docker containers were running). Rewriting was only needed for development, where the frontend and backend are running on different ports.

## Nginx

Referenced more articles online for writing the configuration file [[2](https://medium.com/mitb-for-all/nginx-the-single-server-swiss-army-knife-3445197f8f86)]. Also, relative paths in the nginx bind mount ended up breaking deployment, so I had to create a new directory with a separate Dockerfile for the nginx service.

Initially, the nginx service was tied together with the PitStop app. While this is more than sufficient for a running a single app, the nginx service ends up being tightly coupled with this app. If I were to deploy other apps on my server in the future, this approach of an nginx instance per app would not be feasible. Hence, I split up the nginx service to be a standalone one that serves as the gateway network on my Docker VM, so that deploying other apps in the future only requires a modification of the nginx configuration file.
