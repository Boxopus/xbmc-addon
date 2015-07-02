
import sys
import xbmcaddon
import xbmcgui
import xbmcplugin
import urllib
import urlparse
import json
import requests
from resources.lib.mixpanel import Mixpanel


class BoxopusAddon(object):
    apiUrl = 'https://boxopus.com/api/xbmc/'

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.apiKey = self.addon.getSetting('apiKey')
        self.addonName = self.addon.getAddonInfo('name')
        self.addonUrl = sys.argv[0]
        self.addonHandle = int(sys.argv[1])
        self.addonArgs = urlparse.parse_qs(sys.argv[2][1:])
        self.addonContentType = self.addonArgs.get('content_type', ['video'])[0]
        self.mixpanel = Mixpanel('8bb5f7d783f90afc3cd7979aa9b05877')
        xbmcplugin.setContent(self.addonHandle, 'movies')

    def run(self):
        try:
            mode = self.addonArgs.get('mode', ['home'])[0]
            if mode == 'home':
                self.mixpanel.track(self.apiKey, 'Open XBMC Addon')
                files = self.request(self.build_url(self.apiUrl, {
                    'apiKey': self.apiKey, 'contentType': self.addonContentType}))
                for file in files:
                    url = self.build_url(self.addonUrl, {'mode': 'dir', 'id': file['id']})
                    li = xbmcgui.ListItem(file['name'], iconImage='DefaultFolder.png')
                    xbmcplugin.addDirectoryItem(handle=self.addonHandle, url=url, listitem=li, isFolder=True)
                xbmcplugin.endOfDirectory(self.addonHandle)
            elif mode == 'dir':
                content = self.addonArgs.get('content', ['none'])[0]
                if content == 'none':
                    hash = self.addonArgs.get('id')[0]
                    response = self.request(self.build_url(self.apiUrl + hash, {
                        'apiKey': self.apiKey, 'contentType': self.addonContentType}))
                    files = response['files']
                else:
                    files = json.loads(content)

                if 'dirs' in files and len(files['dirs']) > 0:
                    for dirName, dirContent in files['dirs'].iteritems():
                        url = self.build_url(self.addonUrl, {'mode': 'dir', 'content': json.dumps(dirContent)})
                        li = xbmcgui.ListItem(dirName, iconImage='DefaultFolder.png')
                        xbmcplugin.addDirectoryItem(handle=self.addonHandle, url=url, listitem=li, isFolder=True)

                if 'files' in files:
                    for file in files['files']:
                        li = xbmcgui.ListItem(file['name'], iconImage='DefaultVideo.png')
                        xbmcplugin.addDirectoryItem(handle=self.addonHandle, url=file['path'], listitem=li)
                xbmcplugin.endOfDirectory(self.addonHandle)
        except Exception as e:
            xbmcgui.Dialog().ok(self.addonName, 'Error: ' + e.message)

    def request(self, url):
        r = requests.get(url)
        response = json.loads(r.content)

        if response['status'] == 'error':
            raise Exception(response['data'])
        return response['data']

    def build_url(self, url, query):
        return '%s?%s' % (url, urllib.urlencode(query))


boxopusAddon = BoxopusAddon()
boxopusAddon.run()