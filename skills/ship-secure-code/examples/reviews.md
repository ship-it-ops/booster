# Two security reviews in the default format

These show tone and proportion for a plain "review this" with no other instructions. When a caller asks for another format, use theirs.

## A change with real problems

The request: "Review my branch, it adds invoice downloads." The project's `SECURITY.md` says every invoice route uses `requireInvoiceAccess`, which loads the invoice and checks it belongs to the caller's organisation.

```diff
@@ src/routes/invoices.ts
 21  router.get("/invoices/:id", requireInvoiceAccess, showInvoice);
 22 +router.get("/invoices/:id/pdf", requireLogin, async (req, res) => {
 23 +  const invoice = await db.invoices.findById(req.params.id);
 24 +  const file = path.join(PDF_DIR, invoice.pdfName);
 25 +  res.sendFile(file);
 26 +});
 27 +router.get("/invoice-exports", requireLogin, async (req, res) => {
 28 +  const rows = await db.query(
 29 +    `SELECT id, total FROM invoices WHERE org_id = $1 ORDER BY ${req.query.sort ?? "id"}`,
 30 +    [req.user.orgId]);
 31 +  res.json(rows);
 32 +});
```

The review:

> Any signed-in user can download any organisation's invoice PDF, and the export's `sort` parameter is SQL injection. Both have to be fixed before this is merged.
>
> **must-fix**
>
> - `src/routes/invoices.ts:22-26` — the PDF route uses `requireLogin` where the route above it uses `requireInvoiceAccess`, and `findById` has no organisation condition. A user of one organisation requests `/invoices/<id>/pdf` with another organisation's invoice id and receives the file. Traced: `requireLogin` (`src/auth.ts:14`) only checks the session, while `requireInvoiceAccess` (`src/auth.ts:22`) loads the invoice with the caller's organisation. Use `requireInvoiceAccess` and the invoice it loads.
> - `src/routes/invoices.ts:29` — `req.query.sort` is placed in `ORDER BY`. A signed-in user can extract data from any table through a crafted sort expression. The `org_id` value is bound; the sort is not and cannot be. Map the parameter through an allowlist of column names, as `listInvoices` does at line 12.
>
> **consider**
>
> - `src/routes/invoices.ts:24` — `invoice.pdfName` goes into `path.join`. Not reachable today: the name is written only by `generatePdf` (`src/pdf.ts:31`) and is generated. If users are ever allowed to name files, check containment in `PDF_DIR` here.
>
> Already present, not part of this change: `src/routes/invoices.ts:9` logs the full request, including the session cookie.
>
> Examined: the diff, `src/auth.ts`, `src/pdf.ts` and `SECURITY.md`; assumed any customer can sign up for an account. Not opened: the database driver behind `db.query`. Nothing was run. Outside this review: dependencies, deployment, the rest of the service.

What to notice: the first finding is a missing check, found by comparing the new route with its neighbour. Each finding says who can do what. The item that is not reachable today is one optional line that says why. The older problem gets one line. The last line says what the review does not cover.

## An endpoint with nothing wrong

The request: "Is `POST /api/avatar` safe? It takes an upload."

The review:

> I found no vulnerability in this endpoint in what I examined.
>
> What I checked: the route requires a session (`requireLogin`, registered on the router at `src/routes/account.ts:8`; it rejects a request with no valid session at `src/auth.ts:14`) and writes only to the caller's own record. The upload is limited to 2 MB by the parser (`src/upload.ts:5`). The stored name is a generated UUID with an extension chosen from the detected type, not the uploaded name (`src/upload.ts:19-27`), in a directory outside the web root. Files are served back by id through `src/routes/files.ts:14` with a fixed `Content-Type` and `Content-Disposition: attachment`.
>
> Examined: `src/routes/account.ts`, `src/upload.ts`, `src/routes/files.ts`, `src/auth.ts`. Not opened: the type-detection library called at `src/upload.ts:21`. Nothing was run. Outside this review: the image-processing library and its known vulnerabilities, the storage bucket's access policy, the rest of the service.

What to notice: "nothing found" comes with what was checked and what was not, so the reader knows what the sentence covers, and it does not say the endpoint is safe. No hardening list was added to give the answer some length.
