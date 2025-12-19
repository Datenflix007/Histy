# histy-word

Minimal Word add-in task pane for inserting and refreshing histy citations.

## Serve the add-in

The manifest points to `https://localhost:3000`.

One way to host locally with HTTPS:

```powershell
cd histy-word
npx office-addin-dev-certs install
npx http-server . -S -C "$env:APPDATA\\OfficeAddinDevCerts\\localhost.crt" -K "$env:APPDATA\\OfficeAddinDevCerts\\localhost.key" -p 3000
```

If your Word environment allows `http://localhost`, update `manifest.xml` and serve with:

```powershell
python -m http.server 3000
```

## Sideload

1. Ensure the add-in UI is being served (see steps above).
2. In Word, open **Insert > Add-ins > My Add-ins**.
3. Choose **Upload My Add-in** and select `manifest.xml`.
4. Load the add-in and open the task pane.

## Connect

- Ensure `histy-server` is running on `http://localhost:8000`.
- In the task pane, click **Check** to verify connectivity.

