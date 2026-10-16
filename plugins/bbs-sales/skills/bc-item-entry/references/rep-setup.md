# Rep setup for bc-item-entry

For every rep and every customer. Done once per person; after it, Claude runs the skill
under your own Business Central sign-in and nothing here repeats. Anything marked
**[verify in BC]** is the likely answer, to be confirmed by the admin on the live tenant
before it is treated as fact. Nothing on this page is specific to one RFP or one customer;
where an example is needed it is labelled as one.

## 1. Your Business Central user and licence (admin confirms)

- You need a BC user of your own (Business Central > Users) tied to your
  `@blackboxsafety.com` account. The item card then records you as the creator and the
  skill's log matches the card.
- The licence has to be one that can create items. A **Team Member** licence probably
  cannot (it is read-mostly with a short list of editable tables) **[verify in BC]**; an
  Essentials or Premium user can.
- Permission sets, confirmed by the admin on the Users page, must cover:
  - inserting an Item (table 27);
  - the **Item Card** page used through the published `Item_Card_Excel` web service, which
    is how the skill sets Vendor No. and Vendor Item No., since the standard items API does
    not expose them;
  - reading Vendors.
  The likely answer is `D365 ITEM, EDIT` plus a basic set such as `D365 BASIC`
  **[verify in BC]**. The proof is step 5 below, not the name of the set.

## 2. The app registration in Entra (tenant admin confirms, once for everyone)

The skill signs you in through the existing BBS app registration whose client id is in
`bc-connection.json`. Three settings on that app decide whether a rep's sign-in works:

1. **Allow public client flows** is **Yes** (Authentication page). Without it sign-in fails
   with `AADSTS7000218`.
2. **Tenant-wide admin consent** has been granted for the delegated permission
   *Dynamics 365 Business Central / user_impersonation* (API permissions page). Without it
   each rep sees `AADSTS65001` or `AADSTS90094`.
3. Optionally, on the enterprise application, **Assignment required** is **Yes** with a reps
   group assigned, so only listed users can get a token.

Interactive browser sign-in also needs the redirect URI `http://localhost` under the
*Mobile and desktop applications* platform; if it is missing you see `AADSTS50011` and the
script falls back to a device code (`BBS_BC_SIGNIN=device` forces that).

**What a rep is never given:** a connection file containing `BC_CLIENT_SECRET`. The same
app also holds the service principal's secret for Parker's own scripts; that secret stays
with Parker. `bc-connection.json` carries four values and no secret, the script stops if the
file ever holds a fifth key, and the marketplace checker stops a commit that adds one.

## 3. Install the sign-in libraries

Into the interpreter the skill runs with, in your own terminal:

- **Mac:** `/usr/bin/python3 -m pip install --user msal msal-extensions`
  (use `/usr/bin/python3` for every command here; the python.org build fails TLS
  verification against Microsoft's endpoints).
- **Windows:** `python -m pip install msal msal-extensions`

`scripts/bbs-setup.sh` and `scripts/bbs-setup.ps1` install both too. If a library is
missing, the script stops with the exact `pip` command for the interpreter that ran it,
so copy that line rather than this one if they differ.

`msal` does the sign-in. `msal-extensions` encrypts the cached token (Keychain on a Mac,
DPAPI on Windows). Without it the script still runs and says so, keeping the cache in a
0600 file inside a 0700 `~/.bbs`.

## 4. First run: `whoami`, in your own terminal

```bash
python3 "<plugin root>/skills/bc-item-entry/scripts/bc_item_entry.py" whoami
```

Run it in a terminal you are looking at, not inside a Claude session: the first run opens a
browser window for your Microsoft work account, and a device code printed inside a tool
call may not reach you before it expires. Expected output, in order:

```
SIGN IN: a browser window is opening for your Microsoft work account. ...
[auth] delegated, signed in as you@blackboxsafety.com (token cache encrypted (msal-extensions))
[auth] environment Production, company 'Black Box Safety, Inc.' (OData name '...', read from BC)
[auth] connection values: tenantId from bc-connection.json, clientId from bc-connection.json, ...
[path] items (API): PASS
[path] vendors (API): PASS
[path] Item_Card_Excel (OData web service, sets Vendor No.): PASS
[whoami] delegated, signed in as you@blackboxsafety.com; company 'Black Box Safety, Inc.'; the three reads a commit depends on PASS. Next: run check on a one-item test spec.
```

Nothing was written. If a `[path]` line says FAIL, the skill will refuse `check` and
`commit` until it passes; the line names the HTTP code and what it means (section 6).

## 5. Second run: `check` on a one-item test spec

Make a spec with one item whose number does not exist in BC and a real vendor that does.
Example only; replace every value:

```json
{
  "vendorNo": "V#####",
  "vendorName": "Example Vendor",
  "preparedBy": "Your Name",
  "source": "setup test, nothing to commit",
  "items": [{
    "number": "SETUP-TEST-DO-NOT-COMMIT",
    "displayName": "Example Mfr setup test item",
    "manufacturer": "Example Mfr",
    "baseUoM": "EA", "costPer": "EA",
    "unitCost": 1.00, "unitPrice": 2.00,
    "costSource": "setup test 2026-01-01"
  }]
}
```

Find the vendor number by name first (`bc_query_entity` on `vendors`, or the Vendors list
in BC); the example `V#####` is a placeholder and will fail the vendor gate, which is also a
valid test of the gate. Then:

```bash
python3 "<plugin root>/skills/bc-item-entry/scripts/bc_item_entry.py" check /path/to/items-test.json
```

Expected: the same `[auth]` and `[path]` lines as `whoami`, then

```
[pre-flight] 1 rows pass the field rules
[vendor] V##### = 'Example Vendor', <city>, <state>
[duplicate gate] 1 item numbers are free
# Item entry review - items-test.json
... (the review sheet, with "Writes as: delegated, signed in as you@...")
[check] review sheet written to /path/to/items-test.review.md
[check] APPROVAL TOKEN 0123abcd4567. Show the sheet to the rep. Commit only with their name.
```

That proves the whole path short of a write. **Do not run `commit` on the test spec.**
Delete the test spec and its review sheet when done.

## 6. What each failure means

| You see | Meaning | Who fixes it |
|---|---|---|
| `AADSTS65001` / `AADSTS90094` | Admin consent for `user_impersonation` is missing | Tenant admin (section 2, item 2) |
| `AADSTS50020` | You signed in with a personal or outside account | You: use the work account |
| `AADSTS700016` | Client id or tenant not found | Check `bc-connection.json` or your `BC_*` overrides |
| `AADSTS53003` | Conditional Access blocks this flow | Tenant admin |
| `AADSTS7000218` | Public client flows are off on the app | Tenant admin (section 2, item 1) |
| `AADSTS50011` | `http://localhost` redirect URI missing; device code still works | Tenant admin; you: `BBS_BC_SIGNIN=device` |
| `expired_token` | The sign-in code timed out | You: run again in your own terminal |
| `[path] ... FAIL HTTP 401` | BC has no user for this account, or no licence | BC admin (section 1) |
| `[path] ... FAIL HTTP 403` | Permission set lacks item insert, the Item Card page, or vendor read | BC admin (section 1) |
| `[path] Item_Card_Excel ... FAIL` while items PASS | The Item Card web service is unpublished or your set lacks the page; a commit would create items with no vendor, so the skill refuses | BC admin |
| `CERTIFICATE_VERIFY_FAILED` | Mac, python.org build | You: `/usr/bin/python3` |
| `No module named 'msal'` | Library not installed in this interpreter | You: run the printed pip command |
| `more than one cached sign-in` | Two accounts cached | You: `--account you@blackboxsafety.com`, or `logout --account <other>` |

## 7. Day to day

- Claude runs `check` and `commit` for you; the cached sign-in means no prompt. Every run of
  the script still waits for your Allow click, by ruling: it is not on the `bbs-fill`
  allow list.
- Signing out: `bc_item_entry.py logout` (one cached account) or `logout --all`.
- A new laptop repeats sections 3 to 5. Sections 1 and 2 are per user and per tenant, not
  per machine.
