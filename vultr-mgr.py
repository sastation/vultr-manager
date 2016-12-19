# coding: utf-8

import sys, requests, socket
import json

# OS is OSID: https://api.vultr.com/v1/os/list
# Location is DCID: https://api.vultr.com/v1/regions/list
# Pay model is VPSPLANID: https://api.vultr.com/v1/plans/list

class VultrManager():

    def __init__(self):
        self.loadConf()

    def loadConf(self):
        fs = open('vultr-mgr.conf', 'r')
        lines = fs.readlines()
        content = ''.join(lines)
        fs.close()
        conf = json.loads(content)
        self.PROXIES = {"http": conf['proxy'], "https": conf['proxy']}
        self.LOCATION = conf['location']
        self.SSHKEYID = conf['sshid']
        self.SCRIPTID = conf['scriptid']
        self.APIKEY = {'API-KEY': conf['key']}
        self.SNAPSHOTID = conf['snapshotid']
        self.APIURL = conf['apiurl']
        self.OSID = conf['os']
        self.PAY = conf['pay']

    def listOS(self):
        url = self.APIURL + "/os/list"
        res = requests.get(url, proxies = self.PROXIES)
        print "OS: ", json.dumps(res.json(), sort_keys=True, indent=2)

    def listLocation(self):
        url = self.APIURL + "/regions/list"
        res = requests.get(url, proxies = self.PROXIES)
        print "Locations: ", json.dumps(res.json(), sort_keys=True, indent=2)

    def listPay(self):
        url = self.APIURL + "/plans/list"
        res = requests.get(url, proxies = self.PROXIES)
        print "Pay Plans: ", json.dumps(res.json(), sort_keys=True, indent=2)

    def listSSHKey(self):
        url = self.APIURL + "/sshkey/list"
        res = requests.get(url, headers = self.APIKEY, proxies = self.PROXIES)
        print "SSH keys: ", json.dumps(res.json(), sort_keys=True, indent=2)

    def listScriptID(self):
        url = self.APIURL + "/startupscript/list"
        res = requests.get(url, headers = self.APIKEY, proxies = self.PROXIES)
        print "Scripts: ", json.dumps(res.json(), sort_keys=True, indent=2)

    def listSnapshot(self):
        url = self.APIURL + "/snapshot/list"
        res = requests.get(url, headers = self.APIKEY, proxies = self.PROXIES)
        print "Snapshots: ", json.dumps(res.json(), sort_keys=True, indent=2)

    def listServers(self, mode='p'):
        # "p" is print mode, other is return mode
        url = self.APIURL + "/server/list"
        res = requests.get(url, headers = self.APIKEY, proxies = self.PROXIES)
        if mode == "p":
            servers = res.json()
            for server in servers:
                serverid = server
                hostname = servers[serverid]["label"]
                location = servers[serverid]["location"]
                ip = servers[serverid]["main_ip"]
                status = servers[serverid]["status"]
                state = servers[serverid]["server_state"]
                print ("%s, %s, %s, %s, %s, %s") % (hostname, serverid, ip, status, state, location)
        else:
            return res.json()

    def serverInfo(self, mid):
        servers = self.listServers('r')
        for server in servers:
            serverId = server
            hostname = servers[serverId]["label"]
            hostId = hostname.split("-")[-1]
            if hostId == mid:
                for info in servers[serverId]:
                    print info + "\t" + str(servers[serverId][info])

    def getServerID(self, mid):
        servers = self.listServers('r')
        for server in servers:
            serverId = server
            hostname = servers[serverId]["label"]
            hostId = hostname.split("-")[-1]
            if hostId == mid:
                return serverId, hostname
        return None, None

    def createServer(self, mid, os=215):
        url = self.APIURL + "/server/create"
        serverId = None
        name = hostGroup + "-" + str(mid)
        argvs = {
            "DCID": self.LOCATION, 
            "OSID": self.OSID, 
            "VPSPLANID": self.PAY, 
            "SCRIPTID": self.SCRIPTID,
            "SSHKEYID": self.SSHKEYID,
            "hostname": name,
            "label": name
        }

        res = requests.post(url, headers = self.APIKEY, data = argvs, proxies = self.PROXIES)
        if res.status_code != 200:
            log = "create server " + name + " failed, " + res.text
            print log
        else:
            serverId = res.json()["SUBID"]
            log = "server " + name + " created, its id is " + serverId
            print log
        return serverId

    def destroyServer(self, mid):
        result = None
        serverId, hostname = self.getServerID(mid)
        url = "https://api.vultr.com/v1/server/destroy"
        data = {"SUBID": serverId}
        res = requests.post(url, headers = self.APIKEY, proxies = self.PROXIES, data = data)
        if res.status_code == 200:
            log = hostname + " destroyed"
            print log
            result = True
        else:
            log = "Failed, status code: " + str(res.status_code)
            print log
        return result

    def rebootServer(self, mid):
        result = None
        serverId, hostname = self.getServerID(mid)
        url = "https://api.vultr.com/v1/server/reboot"
        data = {"SUBID": serverId}
        res = requests.post(url, headers = self.APIKEY, proxies = self.PROXIES, data = data)
        if res.status_code == 200:
            log = hostname + " rebooted"
            print log
            result = True
        else:
            log = "Failed, status code: " + str(res.status_code)
            print log
        return result
   
    def updateScript(self):
        url = "https://api.vultr.com/v1/startupscript/update"
        with open("vultr-initial.sh", "r") as f:
            script = f.read()
        data = {
            "SCRIPTID": self.SCRIPTID,
            "name": "default",
            "script": script
        }
        res = requests.post(url, headers = self.APIKEY, proxies = self.PROXIES, data = data)
        if res.status_code == 200:
            log = str(self.SCRIPTID) + " updated"
            print log
        else:
             print res.status_code

    def createServerFromSnapshot(self, mid):
        url = "https://api.vultr.com/v1/server/create"
        serverId = None
        name = hostGroup + "-" + str(mid)
        argvs = {
            "DCID": self.LOCATION, 
            "OSID": 164, # 164: snapshot 
            "VPSPLANID": self.PAY, 
            "hostname": name,
            "label": name,
            "SNAPSHOTID": "1d358569e8bc1"  # 1d358569e8bc1: U16.04-BBR
        }

        res = requests.post(url, headers = self.APIKEY, data = argvs, proxies = self.PROXIES)
        if res.status_code != 200:
            log = "create server " + name + " failed, " + res.text
            print log
        else:
            serverId = res.json()["SUBID"]
            log = "server " + name + " created, its id is " + serverId
            print log
        return serverId

    def reinstallServer(self, mid):
        url = "https://api.vultr.com/v1/server/os_change"
        serverId, hostname = self.getServerID(mid)
        data = {"SUBID": serverId, "OSID": self.OSID} 
        res = requests.post(url, headers = self.APIKEY, data = data, proxies = self.PROXIES)
        if res.status_code == 200:
            log = hostname + " reinstalled"
            print log
            result = True
        else:
            log = "Failed, status code: " + str(res.status_code)
            print log
        return res

# Main funciton
if __name__ == "__main__":
    hostGroup = "vultr"
    mode = sys.argv[1]
    vultrManager = VultrManager()
    if mode == "ssh":
        vultrManager.listSSHKey()
    elif mode == "location":
        vultrManager.listLocation()
    elif mode == "os":
        vultrManager.listOS()
    elif mode == "pay":
        vultrManager.listPay()
    elif mode == "snapshot":
        vultrManager.listSnapshot()
    elif mode == "script":
        try:
            action = sys.argv[2]
        except IndexError:
            action = 'list'

        if action == "list":
            vultrManager.listScriptID()
        elif action == "update":
            vultrManager.updateScript()
    elif mode == "server":
        try:
            action = sys.argv[2]
        except IndexError:
            action = 'list'

        if action == "list":
            vultrManager.listServers('p')
        elif action == "info":
            mid = sys.argv[3]
            vultrManager.serverInfo(mid)
        elif action == "create":
            mid = sys.argv[3] 
            vultrManager.createServer(mid)
        elif action == "destroy":
            mid = sys.argv[3] 
            vultrManager.destroyServer(mid)
        elif action == "reboot":
            mid = sys.argv[3] 
            vultrManager.rebootServer(mid)
        elif action == "create2":
            mid = sys.argv[3]
            vultrManager.createServerFromSnapshot(mid)
        elif action == "reinstall":
            mid = sys.argv[3]
            vultrManager.reinstallServer(mid)
    
    else:
        print "Wrong command."

# End
