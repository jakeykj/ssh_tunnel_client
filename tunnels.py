#!python
import os
from shutil import copyfile
from subprocess import Popen, PIPE, call
from rumps.rumps import MenuItem
import yaml
import rumps

# rumps.debug_mode(True)

class Tunnel:
    def __init__(self, ssh_options, host, user, idfile, forwards, name=None, proxy=None):
        self.ssh_options = ssh_options
        self.name = name if name is not None else host
        self.host = host
        self.user = user
        self.idfile = idfile
        self.forwards = forwards
        self.ssh_command = ['ssh', '-i', idfile]
        for x in forwards:
            self.ssh_command += ['-L', '%s:%s' % (x["local"], x["remote"])]
        if proxy is not None:
            ssh_options['ProxyCommand'] = 'ssh -i {} -W %h:%p {}@{}'.format(idfile, user, proxy)
        for k, v in ssh_options.items():
            self.ssh_command += ['-o', '{}={}'.format(k, v)]
        self.ssh_command += ['{}@{}'.format(user, host)]
        self.ssh_process = None

    def __connect_host(self):
        return Popen(self.ssh_command, stdin=PIPE, stdout=PIPE)

    def connect(self):
        if not self.is_connected():
            self.ssh_process = self.__connect_host()

    def disconnect(self):
        if isinstance(self.ssh_process, Popen):
            self.ssh_process.terminate()

    def is_connected(self):
        return isinstance(self.ssh_process, Popen) and self.ssh_process.poll() is None


class TaskbarTunnelApp(rumps.App):
    def __init__(self):
        super().__init__('SSH Tunnel', quit_button=None)
        self.icon = './icon_off.png'
        self.config_path = os.path.expanduser('~') + '/.config/tunnels/config.yaml'
        self.configs = None
        self.tunnels = None
        self.menu = []

        self.reset()

    def reset(self):
        self.configs = self.load_or_create_config()

        self.tunnels = dict()
        for tunnel_param in self.configs['tunnels']:
            options = self.configs['global']['sshoptions']
            if 'sshoptions' in tunnel_param.keys():
                options.update(tunnel_param['sshoptions'])
            self.tunnels[tunnel_param.get('name', tunnel_param['host'])] = self.create_tunnel(options, tunnel_param)

        pretunnel_items = [rumps.MenuItem('Open configuration', callback=self.open_configuration),
                           rumps.MenuItem('Reload configuration', callback=self.reload_configuration),
                           None,
                           rumps.MenuItem('Connect All', callback=self.connect_all),
                           rumps.MenuItem('Disconnect All', callback=self.disconnect_all),
                           None]

        tunnel_items = [[rumps.MenuItem(name, icon='./red_dot.png', dimensions=(8, 8), callback=self._tunnel_switch),
                         [
                             rumps.MenuItem('(local) %s -> (remote) %s' % (x['local'], x['remote']))
                             for x in self.tunnels[name].forwards
                         ]]
                        for name in self.tunnels]

        posttunnel_items = [None, rumps.MenuItem('Quit', callback=self.quit)]

        self.menu.clear()
        self.menu = pretunnel_items + tunnel_items + posttunnel_items

        if self.configs['global']['connect_all_at_start']:
            self.connect_all()

    def load_or_create_config(self):
        config_dir = os.path.dirname(self.config_path)
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)
        if not os.path.isfile(self.config_path):
            copyfile('./config_template.yaml', self.config_path)
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def create_tunnel(self, sshoptions, tunnel_param):
        return Tunnel(sshoptions,
                      name=tunnel_param.get('name', None),
                      host=tunnel_param['host'],
                      user=tunnel_param['user'],
                      idfile=tunnel_param['identityfile'],
                      forwards=tunnel_param['forwards'],
                      proxy=tunnel_param.get('proxyjump', None))

    def _tunnel_switch(self, sender):
        name = sender.title
        if self.tunnels[name].is_connected():
            self._disconnect_single_tunnel(sender)
        else:
            self._connect_single_tunnel(sender)

    def set_tunnel_icon(self, itemname, switchedon):
        icon = './green_dot.png' if switchedon else './red_dot.png'
        self.menu[itemname].set_icon(icon, dimensions=(8, 8))

    def _connect_single_tunnel(self, sender):
        name = sender.title
        self.tunnels[name].connect()
        self.set_tunnel_icon(name, True)

    def _disconnect_single_tunnel(self, sender):
        name = sender.title
        self.tunnels[name].disconnect()
        self.set_tunnel_icon(name, False)

    def connect_all(self, sender=None):
        for name, t in self.tunnels.items():
            t.connect()
            self.set_tunnel_icon(name, True)
        # self.icon = './icon_green.png'

    def disconnect_all(self, sender=None):
        for name, t in self.tunnels.items():
            t.disconnect()
            self.set_tunnel_icon(name, False)

    @rumps.timer(2)
    def check_status(self, sender):
        tunnel_on = {}
        for name, t in self.tunnels.items():
            if t.is_connected():
                tunnel_on[name] = True
                self.set_tunnel_icon(name, True)
            else:
                tunnel_on[name] = False
                self.set_tunnel_icon(name, False)
        if any([t.is_connected() for _, t in self.tunnels.items()]):
            self.icon = './icon_on.png'
        else:
            self.icon = './icon_off.png'

    def open_configuration(self, sender):
        call(['open', self.config_path])

    def reload_configuration(self, sender):
        self.disconnect_all()
        self.reset()

    def quit(self, sender):
        self.disconnect_all()
        rumps.quit_application()

if __name__ =="__main__":
    app = TaskbarTunnelApp()
    app.run()
