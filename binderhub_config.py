import os
from stat import S_ISDIR, S_IROTH, S_IXOTH
import string
import yaml
from traitlets import Dict, List, Unicode
from kubernetes import client
from binderhub.app import BinderHub
from binderhub.repoproviders import RepoProvider, GitHubRepoProvider, GistRepoProvider, GitRepoProvider, GitLabRepoProvider

# A (v)formatter that removes used keys from its arguments
class ConsumingFormatter(string.Formatter):
    def check_unused_args(self, used_args, args, kwargs):
        ints = []
        for key in used_args:
            if isinstance(key, int):
                ints.append(key)
            else:
                del kwargs[key]
        ints.sort(reverse=True)
        for key in ints:
            args.pop(key)

class LocalDirRepoProvider(RepoProvider):
    allowed_paths = List(
        config = True,
        help="""
        Path prefixes that are allowed to be used.
        By default, none are allowed.  Set to ['/'] to allow all.
        """)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        path = self.spec
        if not path.startswith('/'):
            path = '/' + path
        path = os.path.normpath(path)
        if not any(path.startswith(a) for a in self.allowed_paths):
            raise ValueError('path not allowed')
        self.path = path

    def get_mounts(self):
        mounts = {}
        for ent in os.scandir(self.path):
            if ent.is_symlink() and ent.is_dir():
                mounts[ent.name] = os.readlink(ent.path)
        return mounts
    
    def get_repo_url(self):
        return self.path

    def get_build_slug(self):
        return self.path

    # TODO

class CuratedRepoProvider(RepoProvider):
    """Curated meta-repo provider.

    This provider uses a meta-config that contains the specifications for other repositories.
    This can be used as a level of indirection to restrict what can be launched.
    """

    name = Unicode('Curated')

    config_path = Unicode(
        config=True,
        help="""
        Path to the configuration.
        {N} is expanded to the Nth component of the repo specification.
        Remaining unused components are then looked up in the indicated directory or yaml file.""")

    providers = Dict(#BinderHub.repo_providers.default_value,
        {
            'gh': GitHubRepoProvider,
            'gist': GistRepoProvider,
            'git': GitRepoProvider,
            'gl': GitLabRepoProvider,
            'dir': LocalDirRepoProvider
        },
        config=True,
        help="""Repo Providers to register""")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        safe_chars = frozenset(string.ascii_letters + string.digits + '-_/')
        if set(self.spec) - safe_chars:
            raise ValueError('Invalid characters in spec')

        params = self.load_params()
        provider = self.providers[params.get('provider', 'gh')]
        try:
            spec = params['spec']
        except KeyError:
            spec = params['repo'] + '/' + params.get('branch', 'master')
        self.provider = provider(config = self.config, spec = spec)

        try:
            self.mounts = params['mounts']
        except KeyError:
            try:
                self.mounts = self.provider.get_mounts()
            except AttributeError:
                self.mounts = {}
        for (mount, path) in self.mounts.items():
            self.check_mount(path)

    def load_params(self):
        spec = list(filter(None, self.spec.split('/')))
        path = ConsumingFormatter().vformat(self.config_path, spec, {})

        params = None
        while params is None:
            stat = os.lstat(path)
            if S_ISDIR(stat.st_mode):
                if spec:
                    # recurse into directory
                    h = spec.pop(0)
                    path = os.path.join(path, h)
                else:
                    # treat as repo2docker dir
                    params = {'spec': path, 'provider': 'dir'}
            else:
                # load yaml file
                with open(path) as f:
                    params = yaml.safe_load(f)
                for p in spec:
                    params = params[p]
                if type(params) is not dict:
                    raise TypeError()
        self.stat = stat
        self.params = params
        return params

    def check_mount(self, path):
        s = os.lstat(path)
        if not S_ISDIR(s.st_mode):
            raise NotADirectoryError(path)
        need = S_IROTH | S_IXOTH
        if s.st_uid != self.stat.st_uid and s.st_gid != self.stat.st_gid or s.st_mode & need != need:
            raise PermissionError(path)

    def get_repo_url(self):
        return self.provider.get_repo_url()

    async def get_resolved_ref(self):
        return await self.provider.get_resolved_ref()

    def get_build_slug(self):
        return self.provider.get_build_slug()

    def get_launch_options(self):
        options = {'volumes': [], 'volume_mounts': []}
        for idx, (mount, path) in enumerate(self.mounts.items(), 1):
            name = 'mount%d'%idx
            if not mount.startswith('/'):
                mount = '/home/jovyan/' + mount
            options['volumes'].append(client.V1Volume(name=name, host_path=client.V1HostPathVolumeSource(path=path, type='Directory')).to_dict())
            options['volume_mounts'].append(client.V1VolumeMount(name=name, mount_path=mount, read_only=True).to_dict())
        return options

c.BinderHub.hub_api_token = os.environ['JUPYTERHUB_API_TOKEN']
c.BinderHub.hub_url = os.environ['JUPYTERHUB_URL']
c.BinderHub.image_prefix = os.environ['DOCKER_REGISTRY'] + '/binder-'
c.BinderHub.use_registry = True
c.BinderHub.build_namespace = 'binder'
c.BinderHub.template_path = 'templates'
c.BinderHub.repo_providers = {'fi': CuratedRepoProvider}
c.CuratedRepoProvider.config_path = '/mnt/home/{0}/public_binder'
c.LocalDirRepoProvider.allowed_paths = ['/mnt/home/']
c.DockerRegistry.token_url = ''
c.KubeSpawner.cpu_limit = 0.5
c.KubeSpawner.mem_limit = '1G'
