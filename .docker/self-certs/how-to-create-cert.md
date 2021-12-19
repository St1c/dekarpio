1. First, lets create a root CA cert using createRootCA.sh:

```bash
#!/usr/bin/env bash
openssl genrsa -des3 -out rootCA.key 2048
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 1024 -out rootCA.pem
```

2.Create the openssl configuration file server.csr.cnf referenced in the openssl:
```bash
[req]
default_bits = 2048server
prompt = no
default_md = sha256
distinguished_name = dn

[dn]
C=AT
ST=Austria
L=Wien
O=AIT
OU=Technology Experience
emailAddress=bruno.gardlo@ait.ac.at
CN = localhost
```

3.Now we need to create the v3.ext file in order to create a X509 v3 certificate instead of a v1 which is the default when not specifying a extension file:

```bash
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
```

4.Next, create a file createselfsignedcertificate.sh:

```bash
#!/usr/bin/env bash
sudo openssl req -new -sha256 -nodes -out server.csr -newkey rsa:2048 -keyout server.key -config server.csr.cnf

sudo openssl x509 -req -in server.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out server.crt -days 500 -sha256 -extfile v3.ext
```


5.In order to create your cert, first run createRootCA.sh which we created first. Next, run createselfsignedcertificate.sh to create the self signed cert using localhost as the SAN and CN.

After adding the rootCA.pem to the list of your trusted root CAs, you can use the server.key and server.crt in your web server and browse https://localhost using Chrome 58 or later: