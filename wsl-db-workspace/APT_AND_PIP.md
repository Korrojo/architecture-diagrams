# WSL APT and pip Setup on Restricted Networks

This guide documents a generic setup for installing Python virtual-environment support and Python packages in WSL when proxy settings interfere with package downloads.

Only use direct network access or proxy overrides when permitted by the organization that manages the computer. Prefer an approved proxy, internal package mirror, and approved certificate authority.

## 1. Update APT without the configured proxy

The following override applies only to the current APT command; it does not change persistent proxy configuration:

```bash
sudo apt update \
  -o Acquire::http::Proxy="" \
  -o Acquire::https::Proxy=""
```

## 2. Install virtual-environment and certificate support

```bash
sudo apt install python3-venv ca-certificates \
  -o Acquire::http::Proxy="" \
  -o Acquire::https::Proxy=""
```

If the distribution requires a version-specific package, replace `python3-venv` with the package reported by Python, such as `python3.X-venv`.

To refresh the installed Linux certificate bundle:

```bash
sudo apt install --reinstall ca-certificates \
  -o Acquire::http::Proxy="" \
  -o Acquire::https::Proxy=""
```

## 3. Create and activate a project virtual environment

Run these commands from the project repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Do not use `sudo pip` or `--break-system-packages` inside a virtual environment.

## 4. Install project packages without inherited proxy variables

The following command removes proxy variables only for this pip process:

```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
    -u all_proxy -u ALL_PROXY -u PIP_PROXY \
    python -m pip install pymongo python-dotenv requests
```

## 5. Handle corporate certificate inspection securely

If pip reports `CERTIFICATE_VERIFY_FAILED`, obtain the approved CA certificate or internal Python package index from the support team. Keep TLS verification enabled:

```bash
python -m pip install \
  --cert /path/to/approved-ca-bundle.pem \
  pymongo python-dotenv requests
```

Pip also supports the `PIP_CERT` environment variable when an approved CA bundle should be used for several commands.

## Temporary trusted-host fallback

Some managed environments explicitly authorize a temporary trusted-host workaround:

```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
    -u all_proxy -u ALL_PROXY -u PIP_PROXY \
    python -m pip install pymongo python-dotenv requests \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org
```

`--trusted-host` weakens TLS certificate validation for the named hosts. Use it only with explicit authorization, never as a permanent configuration, and never in automation or production build pipelines.

## Verify the environment

```bash
python -m pip show pymongo python-dotenv requests
python -c "import pymongo, dotenv, requests; print('Dependencies available')"
```

