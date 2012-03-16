#!/usr/bin/env python
import os, sys, json, shutil
import argparse
import prettytable as pt
from progressbar import Counter, ProgressBar, Timer

# set mtfPath
MTFPATH = os.getenv("MTFPATH")

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
p_list.add_argument('-l', type=int, help='max count of nodes listed')
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
p_replace = subparsers.add_parser('user-create', description="Create new Shock user", help='create new Shock user')
p_replace.add_argument('--admin', action='store_true', help='makes new user an admin')

# user-get -h
p_replace = subparsers.add_parser('user-get', description="Get a Shock user details", help='get a Shock user details')

# users-list -h
p_add = subparsers.add_parser('users-list', description="List users. Must be an admin user.", help='list users (admin only)')

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


def main():
	global MTFPATH
	args = parser.parse_args()

	if args.MTFPATH:
		MTFPATH = args.MTFPATH
				
	if not MTFPATH:
		print parser.print_usage()
		print "mtf: err: MTFPATH not set"
		sys.exit()

	#print args
	if args.command == "init":
		if os.path.exists("%s/mtf.cache.json" % MTFPATH):
			os.unlink("%s/mtf.cache.json" % MTFPATH)	
		mtfCache = loadMtf(True)
		
	elif args.command == "list":
		mtfCache = loadMtf()
		table = ""
		if not args.mtfId:
			table = pt.PrettyTable(["id", "providers", "file count", "size"])
			table.set_field_align("id", "l")			
			table.set_field_align("size", "r")
			for k, v in mtfCache.iteritems():
				table.add_row([k, ", ".join(v["providers"].keys()), v["fileCount"], convert_bytes(v["size"])])
		else:
			mtf = mtfCache[args.mtfId]
			table = pt.PrettyTable(["file", "size", "format", "compression", "url"])
			table.set_field_align("file", "l")
			table.set_field_align("size", "r")
			table.set_field_align("format", "l")
			table.set_field_align("url", "l")			
			table.add_row(["%s.spec" % args.mtfId, "", "spec", "", ""])
			for i in mtf["metadata"]:
				table.add_row([i, "", "json","", ""])			
			if mtf.has_key("raw"):
				for r, rv in mtf["raw"].iteritems():
					size = convert_bytes(rv["size"]) if rv.has_key("size") else "n/a"
					table.add_row(["raw/%s" % r, size, "fasta", (rv["compression"] or ""), (rv["url"] or "")])	
			for p, v in sorted(mtf["providers"].iteritems()):
				for f, fv in sorted(v["files"].iteritems()):
					size = convert_bytes(fv["size"]) if fv.has_key("size") else "n/a"
					table.add_row(["%s/%s" % (p, f), size, fv["type"], (fv["compression"] or ""), (fv["url"] or "")])								
		print table	
		
	elif args.command == "get":
		mtfCache = loadMtf()
	 	toDo= {"id" : None, "mtf" : None, "path" : args.target_dir, "mkdir" : [], "download" : [], "copy" : []}
		if args.mtf.count("/") > 0:
			if args.mtf.count("/") == 1:
				[toDo["id"], rest] = args.mtf.split("/")
				toDo["mtf"] = mtfCache[toDo["id"]]
				if rest == "raw":
					toDo["mkdir"].append("raw")
					for f, v in toDo["mtf"]["raw"].iteritems():
						toDo["download"].append([f, "raw", v["url"]])
				elif rest in toDo["mtf"]["providers"].keys():
					toDo["mkdir"].append(rest)
					for f, v in toDo["mtf"]["providers"][rest]["files"].iteritems():
						toDo["download"].append([f, rest, v["url"]])
				elif "spec" in rest.split(".") or "metadata" in rest.split("."):
					toDo["copy"].append([rest, rest,""])
			elif args.mtf.count("/") == 2:
				[toDo["id"], d, f] = args.mtf.split("/")
				toDo["mtf"] = mtfCache[toDo["id"]]
				if d == "raw" and f in toDo["mtf"]["raw"].keys():
					toDo["mkdir"].append("raw")
					toDo["download"].append([f, "raw", toDo["mtf"]["raw"][f]["url"]])
				elif d in toDo["mtf"]["providers"].keys():
					toDo["mkdir"].append(d)
					if f in toDo["mtf"]["providers"][d]["files"].keys():
						toDo["download"].append([f, d, toDo["mtf"]["providers"][d]["files"][f]["url"]])
					
			elif args.mtf.count("/") > 2:
				# error?
				print "invalid mtf path"
				pass
		else:
			toDo["id"] = args.mtf
			toDo["mtf"] = mtfCache[toDo["id"]]
			toDo["copy"].append(["%s.spec" % toDo["id"] , "%s.spec" % toDo["id"], ""])
			toDo["mkdir"].append("raw")			
			for m in toDo["mtf"]["metadata"]:
				toDo["copy"].append([m, m, ""])
			for r, rv in toDo["mtf"]["raw"].iteritems():
				toDo["download"].append([r, "raw", rv["url"]])
			for p, pv in toDo["mtf"]["providers"].iteritems():
				toDo["mkdir"].append(p)
				for f, fv in pv["files"].iteritems():
					toDo["download"].append([f, p, fv["url"]])
						
		#toDo["mtf"] = None
		#print toDo
		performGet(toDo)
		#mtf = mtfCache[mtfId]
		#print mtf
		
		# u = urllib.urlopen("http://api.metagenomics.anl.gov/Metagenome/%s" % (mgid))
		# u.read()

	elif args.command == "replace-spec":
		print "Not implemented yet."
	elif args.command == "add-provider":
		print "Not implemented yet."
		
	sys.exit()

if __name__ == '__main__':
    main()
