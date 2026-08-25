# Azure App Service deployment

Use a Linux App Service with Python 3.13 and set the startup command to:

```text
sh startup.sh
```

## Required app settings

Configure these in App Service **Settings > Environment variables**:

```text
DEBUG=False
SECRET_KEY=<a-long-random-value>
ALLOWED_HOSTS=burgerbills.ws,www.burgerbills.ws,<app-name>.azurewebsites.net
CSRF_TRUSTED_ORIGINS=https://burgerbills.ws,https://www.burgerbills.ws,https://<app-name>.azurewebsites.net
QR_CODE_BASE_URL=https://burgerbills.ws
DATABASE_URL=postgresql://<user>:<password>@<server>:5432/<database>
AZURE_STORAGE_CONNECTION_STRING=<storage-account-connection-string>
AZURE_MEDIA_CONTAINER=media
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

Create the `media` Blob container before starting the app. The container may remain private; generated media URLs use signed access tokens.

## Domain and TLS

In **App Service > Custom domains**, add `burgerbills.ws` and optionally `www.burgerbills.ws`, create the DNS records Azure requests, and bind an App Service managed certificate. Enable **HTTPS Only**.

Existing SQLite data and local files are not copied automatically into PostgreSQL or Blob Storage. Export/import any menu data and upload existing files before switching production traffic.