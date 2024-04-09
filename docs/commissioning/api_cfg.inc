.. _apicfgfile-label:

=========================
API configuration file
=========================

To be able to use the IDEAL API interface, the user must customize the ``api.cfg`` file, in the ``cfg`` folder.
The file has two main sections:

[receiver]
``send result``: true or false. If true, the log_daemon will attempt to send the results back. This assumes that there is a 'receiving' API running on the client.
                an example of such an API can be found in ``receiver_test.py`` in the IDEAL's main directory.
``url to send result``: e.g. http://127.0.0.1:3000/api/results
``url authentication``: e.g. http://127.0.0.1:3000/auth. The API uses login data.

[server]
``IP host``: IP address of the server
``credentials db``: .db file containing the authorized users login data and information.
``ssl cert`` : path to the ssl certificate, if needed
``ssl key `` : path to the ssl key, if needed

The API runs by default on the https protocol. Therefore, a self signed certificate and related key should be generated. 
The API can also run on http, with small modifications to the ``bin/api.py`` file. In this case, the ssl certificate and key are not needed. 
For more info, read the dedicated section on the user manual.
