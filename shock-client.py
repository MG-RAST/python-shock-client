#!/usr/bin/env python3

import os
from restclient.restclient import RestClient


# Example constructor with OAuth
c = RestClient("https://shock.mg-rast.org", headers = { "Authorization" : "mgrast "+os.environ['MGRKEY'] })

# err = sc.Put_request("/node/"+node_id+"/acl/public_read", nil, &sqr_p)


# http://shock.mg-rast.org/node/6fa12ee7-8cb6-421e-b6ed-02188cf7117b
node_id = "6fa12ee7-8cb6-421e-b6ed-02188cf7117b"



response = c.put("node/"+node_id+"/acl/public_read", debug=True)

print(response.json())


