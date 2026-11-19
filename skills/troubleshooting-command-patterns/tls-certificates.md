# TLS certificates

### Client fails with `UntrustedRoot` / "cannot establish trust relationship for the SSL/TLS channel" on an internal HTTPS service
- Cause: the server uses its own private root (e.g. vCenter VMCA, appliance self-signed CA), not a CA in the OS/corporate bundle.
- Diagnose (no credentials sent), read the presented chain:
  ```powershell
  $script:els = @(); $cb = [Net.Security.RemoteCertificateValidationCallback]{ param($s,$c,$chain,$e) $script:els = @($chain.ChainElements | % { $_.Certificate }); $true }
  $tcp = [Net.Sockets.TcpClient]::new('<host>', 443); $ssl = [Net.Security.SslStream]::new($tcp.GetStream(), $false, $cb); $ssl.AuthenticateAsClient('<host>'); $ssl.Dispose(); $tcp.Dispose()
  $script:els | % { "$($_.Subject) | issuer=$($_.Issuer) | $($_.Thumbprint) | until $($_.NotAfter)" }
  ```
- Fix: export the root (last element) as PEM and trust it explicitly for that client only, never skip verification:
  `"-----BEGIN CERTIFICATE-----`n$([Convert]::ToBase64String($script:els[-1].RawData,'InsertLineBreaks'))`n-----END CERTIFICATE-----"`
  Go clients: `SSL_CERT_FILE=<pem>`; govc: `GOVC_TLS_CA_CERTS=<pem>`; containers: mount the PEM read-only and set the variable.
- Verify: the client connects; a probe with dummy credentials returns an auth error (not a TLS error).
- Note: the root came over an untrusted connection; confirm the thumbprint with the service owner or its admin UI once.
- Seen: <yyyy-mm-dd>, <context>
