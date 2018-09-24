#!/usr/bin/python
# -*- coding: utf-8 -*-

# Authorization plugin that uses an authDB and grid-mapfile
# usage:
# gridmap_auth.py <clientname> <remoteaddr> <fqan1> .. <fqanN>
#
# Return value means:
# 0 --> access is GRANTED
# nonzero --> access is DENIED
#

import sys, re, json

# A class that implements a grid-mapfile loaded from a text file during the initialization of the module.
class _Authlist(object):
  GridMapFile = "/etc/grid-security/grid-mapfile"
  d = {}

  def __init__(self):
    print "Loading Gridmap file from " + self.GridMapFile
    with open(self.GridMapFile) as f:
      for line in f:
# Gridmap file looks like "/O=dutchgrid/O=users/O=nikhef/CN=Dominik Duda" atlasuser
# Split on '" ' in the middle and then strip of the leading " and trailing \n
        DN = (line.rsplit('" ')[0]).strip('"')
        Role = (line.split('" ')[-1]).strip('\n')
        self.d[DN] = Role
#        print(self.d)

  def authenticateUser(self,DN):
    return DN in self.d

  def getRole(self, DN):
    return self.d[DN]


# A class that implements an authorization database loaded from a json file during the initialization of the module.
class _AuthDB(object):
  AuthDBFile = "/etc/grid-security/authdb.json"
  d = {}

  def __init__(self):
    print "Loading AuthDB file from " + self.AuthDBFile
    with open(self.AuthDBFile) as f:
      self.d = json.load(f)
#    print(self.d)

  def authorizedUsers(self,VO,bucket):
#    print "VO name is " + VO
#    print "Bucket name is " + bucket
    return self.d[VO][bucket]

# Initialize a global instance of the authlist class, to be used inside the isallowed() function
myauthlist = _Authlist()
myauthDB = _AuthDB()

def isallowed(clientname="unknown", remoteaddr="nowhere", resource="none", mode="0", fqans=None, keys=None):
#  print "clientname", clientname
#  print "remote address", remoteaddr
#  print "fqans", fqans
#  print "keys", keys
#  print "mode", mode
#  print "resource", resource

# bucket name can be extracted from resource which looks like: /gridpp/dteam-disk/test1
# Split on '/' and take the 3rd entry
  path = resource.split('/')
# For paths with a trailing / remove final entry.
  if(path[-1] == ''):
    del path[-1]
#  print(path)
# Allow anyone to browse the top level directory (They can see what VO names are)
  if (len(path) <= 3):
    if (mode == 'r' or mode == 'l'):
      return 0
    else:
      return 1
# Return a permission denied if anyone tries to delete a top level directory (ie delete a bucket)
  elif (len(path) == 4 and mode == 'd'):
    return 1
  else:
    VO = path[2]
    bucket = path[3]

  a = {}
  try:
    a = myauthDB.authorizedUsers(VO, bucket)
#    print(a)
  except:
    print "Failed to load authorized Users, denying access"
    return 1;

  for k, v in a.iteritems():
# Check to see if user is in the grid-mapfile
    if (k == "role"):
      try:
        permissions = v[myauthlist.getRole(clientname)]
      except:
#        print "DN not in grid-mapfile"     
        pass
      else:
        if (mode in permissions):
#          print "Role matched " + myauthlist.getRole(clientname)
          return 0

# Check to see if the DN has been added to the authDB
    if (k == "clientname" and clientname in v):
      if (mode in v[clientname]):
#        print "DN matched " + clientname
        return 0

# Check to see if the hostname has been given specific priveleges
    if (k == "remoteaddr" and remoteaddr in v):
      if (mode in v[remoteaddr]):
#        print "Remote IP matched " + remoteaddr
        return 0

# If user is still not authorized: deny access!
  return 1


#------------------------------
if __name__ == "__main__":
  r = isallowed(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
  print r
  sys.exit(r)
