# Google connectors: Search Console and Analytics 4

This repository never includes or connects to its owner's Google accounts. It ships
only connector code and setup instructions; every user supplies their own OAuth
credentials and property identifiers.

## Overview

There are two ways to use the Google data sources:

- **Direct API:** the `seotoolbox/gsc.py` and `seotoolbox/ga4.py` modules use OAuth
  2.0 and return normalized rows to the CLI.
- **MCP:** an MCP server can make the same APIs available to an AI agent such as
  Claude Code, Cursor, or Hermes. Community servers require a separate security and
  maintenance review before use.

| Tool | Direct API endpoint | MCP server | Required OAuth scope |
|---|---|---|---|
| Search Console | `https://www.googleapis.com/webmasters/v3/` | Community GSC server or local CLI wrapper | `https://www.googleapis.com/auth/webmasters.readonly` |
| Google Analytics 4 | `https://analyticsdata.googleapis.com/v1beta/` | Community GA4 server or local CLI wrapper | `https://www.googleapis.com/auth/analytics.readonly` |

## Common prerequisite: Google Cloud Console

1. Open <https://console.cloud.google.com>, then create a project or select an
   existing project.
2. Open **APIs & Services > Library**. Search for and enable **Google Search Console
   API** and **Google Analytics Data API**.
3. Open **APIs & Services > OAuth consent screen**, select **External**, and provide
   an application name and contact email. Add these read-only scopes:
   `https://www.googleapis.com/auth/webmasters.readonly` and
   `https://www.googleapis.com/auth/analytics.readonly`. An application used only
   personally may remain in **Testing** when the Google account is added as a test
   user. Otherwise publish it with status **In production**.
4. Open **APIs & Services > Credentials > Create credentials > OAuth client ID**.
   Select **Desktop app**, create the client, download its JSON file, and extract
   `client_id` and `client_secret`. Do not add this file to the repository.
5. Obtain a refresh token once:
   - Replace `{CLIENT_ID}` and open this authorization URL in a browser:

     ```text
     https://accounts.google.com/o/oauth2/v2/auth?client_id={CLIENT_ID}&redirect_uri=http://localhost&response_type=code&scope=https://www.googleapis.com/auth/webmasters.readonly%20https://www.googleapis.com/auth/analytics.readonly&access_type=offline&prompt=consent
     ```

   - After consent, copy `{CODE}` from the attempted redirect to
     `http://localhost/?code={CODE}`. A local connection error is harmless: the code
     remains in the browser address bar.
   - Exchange that short-lived code immediately:

     ```bash
     curl -X POST https://oauth2.googleapis.com/token \
       -d client_id="$GSC_CLIENT_ID" \
       -d client_secret="$GSC_CLIENT_SECRET" \
       -d code="{CODE}" \
       -d grant_type=authorization_code \
       -d redirect_uri=http://localhost
     ```

     The JSON response contains an `access_token` and a `refresh_token`. Google only
     issues the refresh token when `access_type=offline` is present; `prompt=consent`
     forces a new consent flow when the account has already authorized the client.
6. Export the values in the shell that runs `seo`:

   ```bash
   export GSC_CLIENT_ID="..."
   export GSC_CLIENT_SECRET="..."
   export GSC_REFRESH_TOKEN="..."
   export GA4_PROPERTY_ID="123456789"
   ```

The GSC-named OAuth variables are shared by both connectors because one Google Cloud
OAuth client and refresh token cover both consented scopes. Never commit these values.

## Connect Google Search Console

First verify the site in <https://search.google.com/search-console>. Search Console
supports domain properties such as `sc-domain:example.com` and URL-prefix properties
such as `https://example.com/`.

```bash
seo gsc properties
seo gsc queries --property sc-domain:example.com --days 28
seo gsc pages --property sc-domain:example.com --days 28
```

The property must be available to the Google account that completed OAuth consent.
The exact property string returned by `seo gsc properties` should be used in queries.

## Connect Google Analytics 4

Open <https://analytics.google.com>, select **Admin > Property Settings**, and copy
the numeric property ID. If Google displays `properties/123456789`, export only
`123456789` as `GA4_PROPERTY_ID`. The OAuth account must have access to that property.

```bash
seo ga4 daily --days 28
seo ga4 sources --days 28 --limit 10
seo ga4 pages --days 28 --limit 10
```

## MCP option for AI agents

MCP is useful when an agent should query GSC or GA4 without custom integration code.
Community packages sometimes advertise names such as `gsc-mcp` or
`google-analytics-mcp`, but package names, publishers, permissions, and maintenance
status must be **verified at the time of use**. This guide intentionally does not
provide an unverified install command.

The generic setup is to configure a vetted stdio MCP server in the AI client, pass
the same OAuth values through its environment configuration, and allow only the two
read-only scopes listed above. Review its source and pin a version before running an
`npx` or equivalent command.

A controlled alternative is a small local stdio MCP server that wraps the existing
`seo gsc ...` and `seo ga4 ...` commands. It can publish one read-only tool per CLI
operation, validate arguments, execute the command with JSON output, and return that
JSON over MCP. Credentials stay in the wrapper process environment rather than in
prompts or MCP configuration committed to source control.

## Real-world verification without bundled accounts

The repository is delivered without credentials. In that state,
`seo gsc properties` reports `GSC credentials missing`; `seo ga4 daily` first reports
`GA4_PROPERTY_ID missing`, or `GSC credentials missing` when the property ID alone is
configured. These are expected safe failures.

After configuring all environment variables, run this end-to-end check:

1. `seo gsc properties` lists the expected property.
2. `seo gsc queries --property sc-domain:example.com --days 28` returns genuine
   clicks and impressions (or an empty result if Google has no data for the period).
3. `seo ga4 daily --days 28` returns sessions grouped by date (or an empty result if
   the property has no data for the period).

HTTP 401, 403, and 404 responses are not replaced with fabricated data. The CLI
prints the Google HTTP error and exits non-zero; verify the token, OAuth account,
enabled API, and exact property ID when this occurs.
