#!/usr/bin/env python3

import os, sys
from restclient.restclient import RestClient


# Example constructor with OAuth
c = RestClient("https://shock.mg-rast.org", headers = { "Authorization" : "mgrast "+os.environ['MGRKEY'] })

# err = sc.Put_request("/node/"+node_id+"/acl/public_read", nil, &sqr_p)

for node_id in sys.argv[1:]:

    response = c.put("node/"+node_id+"/acl/public_read", debug=True)

    print(response.json())


