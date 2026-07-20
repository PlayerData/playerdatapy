# FAQ

### Which authentication method should I use?

- **Authorisation Code Grant** — user-facing apps, per-user access
- **Client Credentials Grant** — backend integrations, org-level access

### Why can't I access a club's data?

Using Authorisation Code Grant: the authenticated user/service is not listed as staff for that club. Contact the club administrator to grant access.

### Can I write or update data (mutate) via the API?

Yes — under both the Authorisation Code Grant and the Client Credentials Grant.

### Is the GraphiQL Playground safe to use?

Yes — but mutations run against **real production data**.

### How long do tokens last?

Access tokens expire after **2 hours**. Authorisation Code Grant issues refresh tokens; Client Credentials Grant does not (re-run the flow).

### Where do I get credentials?

Contact your PlayerData representative or `support@playerdata.com`.
