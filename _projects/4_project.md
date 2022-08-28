---
layout: page
title: Automated Certificate Management Environment 
description: Self-contained functional ACME client in Python.
img:
importance: 3
category: Misc.
---

<p align="justify"> This was a course project for the course Network Security at ETH Zurich, in Autumn 2021, where we had to implement a functional ACME client. The <a href="https://tools.ietf.org/html/rfc8555"> Automatic Certificate Management Environment (ACME) protocol </a> aims to facilitate the automation of certificate issuance by creating a standardized and machine-friendly protocol for certificate management. </p>

<p align="justify">The task was to write an application that implements ACMEv2. However, to make the application self-contained and in order to facilitate testing, the application needed to have more functionality than a bare ACME client. The concrete requirements for the application were: </p>

The submitted application consisted of the following components:
- *ACME client:* An ACME client which could interact with a standard-conforming ACME server.
- *DNS server:* A DNS server which resolved the DNS queries of the ACME server.
- *Challenge HTTP server:* An HTTP server to respond to the `http-01` queries of the ACME server.
- *Certificate HTTPS server:* An HTTPS server which used the certificate obtained by the ACME client.
- *Shutdown HTTP server:*  An HTTP server to receive a shutdown signal.

The requirements for the application were to be able to 
- use ACME to request and obtain certificates using the `dns-01` and `http-01` challenge (with fresh keys in every run),
- request and obtain certificates which contain aliases,
- request and obtain certificates with wildcard domain names, and
- revoke certificates after they have been issued by the ACME server.

Implementation of entire project can be found here: <a href="https://github.com/Siddhant-Ray/ACME-Client"> Code </a>