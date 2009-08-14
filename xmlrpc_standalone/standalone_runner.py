#!/usr/bin/python2.4

import daemon
import standalone_xmlrpc



if __name__ == "__main__":
	s = standalone_xmlrpc.StandaloneXMLRPC()
	d = daemon.Daemon(s)
