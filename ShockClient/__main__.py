#!/usr/bin/env python
import os, sys, json, shutil
import argparse
import requests
import prettytable as pt
from progressbar import Counter, ProgressBar, Timer

# get env vars
SHOCKURL = os.getenv("SHOCKURL")
SHOCKUSER = os.getenv("SHOCKUSER")
SHOCKPASSWORD = os.getenv("SHOCKPASSWORD")

# arg type checking
def file_type(f):
	if not os.path.isfile(f):
		msg = "%s is not a file" % f
		raise argparse.ArgumentTypeError(msg)
	else:
		return f

def dir_type(d):
	if not os.path.isdir(d):
		msg = "%s is not a directory" % d
		raise argparse.ArgumentTypeError(msg)
	else:
		return d

# setup option/arg parser
parser = argparse.ArgumentParser(prog='shock', epilog='Use "shock command -h" for more information about a command.')
parser.add_argument('--SHOCKURL', help='Overrules env SHOCKURL')
parser.add_argument('--SHOCKUSER', help='Overrules env SHOCKUSER')
parser.add_argument('--SHOCKPASSWORD', help='Overrules env SHOCKPASSWORD')
subparsers = parser.add_subparsers(dest='command', title='The commands are')

# list -h
p_list = subparsers.add_parser('list', description='Lists the nodes in Shock.', help='list nodes')
p_list.add_argument('-l', type=int, help='limit, the max count of nodes listed')
p_list.add_argument('-s', type=int, help='skip N nodes')
p_list.add_argument('-q', help='Shock query string, in the form of "tag=value[,tag2=value2,..]" see githhub.com/MG-RAST/Shock for more details.')
# p_list.add_argument('-p', action='store_true', help='disables pretty print for ease of parsing and use with other command line utilities')

# get -h
p_get = subparsers.add_parser('get', help='get node or node file')
p_get.add_argument('id', help='Shock id of node')
p_get.add_argument('target', nargs='?', type=dir_type, help='target directory of download. Only used with --download')
p_get.add_argument('--download', action='store_true', help='downloads the node\'s file')

# create -h
p_create = subparsers.add_parser('create', description="Create new node. ", help='create new node')
p_create.add_argument('--file', type=file_type, help='path to file upload')
p_create.add_argument('--attributes', type=file_type, help='path to json attributes file')

# user-create -h
p_create_user = subparsers.add_parser('user-create', description="Create new Shock user", help='create new Shock user')
p_create_user.add_argument('name', help='user name')
p_create_user.add_argument('password', help='password')
p_create_user.add_argument('--admin', help='secret key that makes a new user an admin')

# user-get -h
p_get_user = subparsers.add_parser('user-get', description="Get a Shock user details. Requires SHOCKUSER and SHOCKPASSWORD to be set. Note: only admin user are able to lookup other users by their uuid.", help='get a Shock user details')
p_get_user.add_argument('uuid', help='the uuid of the user')

# users-list -h
p_add = subparsers.add_parser('user-list', description="List users. Requires SHOCKUSER and SHOCKPASSWORD to be set. Note: this is not available to non-admin users.", help='list users (admin only)')

def convert_bytes(n):
    K, M, G, T = 1 << 10, 1 << 20, 1 << 30, 1 << 40
    if   n >= T:
        return '%.1fT' % (float(n) / T)
    elif n >= G:
        return '%.1fG' % (float(n) / G)
    elif n >= M:
        return '%.1fM' % (float(n) / M)
    elif n >= K:
        return '%.1fK' % (float(n) / K)
    else:
        return '%d' % n


def get(url):
	global SHOCKUSER, SHOCKPASSWORD
	r = None
	if SHOCKUSER and SHOCKPASSWORD:
		r = requests.get(url, auth=(SHOCKUSER, SHOCKPASSWORD))
	else:
		r = requests.get(url)
	res = json.loads(r.text)
	return res
	
def post(url, files):
	global SHOCKUSER, SHOCKPASSWORD
	r = None
	if SHOCKUSER and SHOCKPASSWORD:
		r = requests.post(url, auth=(SHOCKUSER, SHOCKPASSWORD), files=files)
	else:
		r = requests.post(url, files=files)
	res = json.loads(r.text)
	return res

def fmtText(text):
	tarray = []
	if len(text) > 100:
		while len(text) > 100:
			tarray.append(text[0:100])
			text = text[100:]
		if len(text) > 0:
			tarray.append(text)
	else:
		tarray.append(text)
	return tarray
	
def printNodeTable(n):
	t = pt.PrettyTable(["name", "key/value", "value"])
	t.set_field_align("name", "l")
	t.set_field_align("key/value", "l")
	t.set_field_align("value", "l")		
	t.add_row(["id",n["id"],""])
	t.add_row(["file","",""])
	for k,v in n["file"].iteritems():
		t.add_row(["",k,json.dumps(v)])
	t.add_row(["indexes",json.dumps(n["indexes"]),""])		
	if n["attributes"] != None:
		t.add_row(["attributes","",""])
		for k,v in n["attributes"].iteritems():
			value = json.dumps(v, sort_keys=True, indent=4)
			split = value.split('\n')
			if len(split) > 1:
				t.add_row(["",k,split[0]])
				for attr in value.split('\n')[1:]:
					for r in fmtText(attr):
						t.add_row(["","",r])
			else:
				t.add_row(["",k,split[0]])
	else:
		t.add_row(["attributes","{}",""])
	t.add_row(["acls","",""])
	for k,v in n["acl"].iteritems():
		val = json.dumps(v) if v != None else "[]"
		t.add_row(["",k,val])		
	print t

def printUserTable(u):
	t = pt.PrettyTable(["name", "value"])
	t.set_field_align("name", "l")
	t.set_field_align("value", "l")	
	t.add_row(["uuid",u["uuid"]])	
	t.add_row(["name",u["name"]])	
	t.add_row(["passwd",u["passwd"]])	
	t.add_row(["admin",u["admin"]])
	print t	

def printUsersTable(u):
	t = pt.PrettyTable(["uuid", "name", "passwd", "admin"])
	t.set_field_align("uuid", "l")
	t.set_field_align("name", "l")	
	t.set_field_align("passwd", "l")
	t.set_field_align("admin", "l")
	
	if len(u) > 0:
		for user in u:
			t.add_row([user["uuid"], user["name"], "**********", user["admin"]])
	print t
					
def main():
	global SHOCKURL, SHOCKUSER, SHOCKPASSWORD
	
	args = parser.parse_args()

	# overwrite env vars in args
	if args.SHOCKURL:
		SHOCKURL = args.SHOCKURL
	if args.SHOCKUSER:
		SHOCKUSER = args.SHOCKUSER				
	if args.SHOCKPASSWORD:
		SHOCKPASSWORD = args.SHOCKPASSWORD				

	if not SHOCKURL:
		print parser.print_usage()
		print "shock: err: SHOCKURL not set"
		sys.exit()
	
	url = "http://%s" % (SHOCKURL)
	if args.command == "list":
		if args.l is None and args.q is None:
			print "warning: list without limit or query make take a long time." 
		url += "/node"
		if args.l or args.s or args.q:
			params = []
			if args.q: params.append("query&%s" % args.q)
			if args.l: params.append("limit=%s" % args.l)
			if args.s: params.append("skip=%s" % args.s)			 			
			url = "%s/?%s" % (url, "&".join(params))
		res = get(url)
		if res["E"] is None:
			t = pt.PrettyTable(["id", "size", "indexes", "attributes"])
			if res["D"] != None:
				for n in res["D"]:
					fileSize = n["file"]["size"] if n["file"]["size"] > 0 else ""
					indexes = n["indexes"] or ""
					attr = json.dumps(n["attributes"], sort_keys=True)
					if len(attr) > 50:
						attr = "%s ...}" % attr[0:50]
					t.add_row([n["id"], fileSize, indexes, attr])
			print t
		else:
			print "shock: err from server: %s" % res["E"][0]

	elif args.command == "get":
		url += "/node/%s" % (args.id)
		url += "?download" if args.download else ""
		res = get(url)
		if res["E"] is None:
			printNodeTable(res["D"])
		else:
			print "shock: err from server: %s" % res["E"][0]
		
	elif args.command == "create":
		url += "/node"
		files = {}
		if args.attributes:
			files["attributes"] = (os.path.basename(args.attributes), open(args.attributes, 'rb'))
		if args.file:
			files["file"] = (os.path.basename(args.file), open(args.file, 'rb'))
		res = post(url, files)
		if res["E"] is None:
			printNodeTable(res["D"])
		else:
			print "shock: err from server: %s" % res["E"][0]
	elif args.command == "user-create":
		url += "/user"
		passwd = args.password
		if args.admin:
			passwd += ":%s" % args.admin
		r = requests.post(url, auth=(args.name, passwd))
		res = json.loads(r.text)	
		if res["E"] is None:
			printUserTable(res["D"])
		else:
			print "shock: err from server: %s" % res["E"][0]
	elif args.command == "user-get":
		url += "/user"
		url += "/%s" % args.uuid
		if not (SHOCKUSER and SHOCKPASSWORD):	
			print "shock: err: SHOCKUSER and/or SHOCKPASSWORD not set"
			sys.exit()
		res = get(url)
		if res["E"] is None:
			printUserTable(res["D"])
		else:
			print "shock: err from server: %s" % res["E"][0]		
	elif args.command == "user-list":
		url += "/user"
		if not (SHOCKUSER and SHOCKPASSWORD):	
			print "shock: err: SHOCKUSER and/or SHOCKPASSWORD not set"
			sys.exit()
		res = get(url)
		if res["E"] is None:
			printUsersTable(res["D"])
		else:
			print "shock: err from server: %s" % res["E"][0]
		
	sys.exit()
	
if __name__ == '__main__':
    main()
