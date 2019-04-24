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
    """Local host directory provider.

    This provider just passes the given local host directory "repo" directly to repo2docker, mounted as a host_path volume.
    """
    name = Unicode('LocalDir')

    allowed_paths = List(
        config = True,
        help="""
        Prefixes for paths that are allowed to be used as repos.
        By default, none are allowed.  Set to ['/'] to allow all.
        """)

    required_marker = Unicode(
        config = True,
        help="""
        If set, a file by this name must exist in any "repo" directory.
        """)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        path = self.spec
        if not path.startswith('/'):
            path = '/' + path
        path = os.path.normpath(path)
        self.allowed_index = next(i for (i, p) in enumerate(self.allowed_paths) if path.startswith(p))
        if not os.path.exists(os.path.join(path, self.required_marker)):
            raise ValueError('path not allowed')
        self.path = path

    def get_repo_url(self):
        return self.path

    def get_build_slug(self):
        return '{0}/{1}'.format(self.allowed_index, self.path[len(self.allowed_paths[self.allowed_index]):])

    async def get_resolved_ref(self):
        s = os.lstat(self.path)
        if not S_ISDIR(s.st_mode):
            raise NotADirectoryError(self.path)
        return format(s.st_ctime_ns, 'x')

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

    allowed_mounts = List(
        config = True,
        help="""
        Prefixes for paths that are allowed to be mounted.
        By default, none are allowed.  Set to ['/'] to allow all.
        """)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        safe_chars = frozenset(string.ascii_letters + string.digits + '-_/')
        if not all(c in safe_chars for c in self.spec):
            raise ValueError('Invalid characters in spec')
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
                    params = {'spec': path, 'provider': 'dir', 'mounts': {}}
                    for ent in os.scandir(path):
                        if not ent.name.startswith('.') and ent.is_symlink() and ent.is_dir():
                            targ = os.readlink(ent.path)
                            if self.check_mount(targ, stat):
                                params['mounts'][ent.name] = targ
            else:
                # load yaml file
                with open(path) as f:
                    params = yaml.safe_load(f)
                for p in spec:
                    params = params[p]
                if type(params) is not dict:
                    raise TypeError(params)

        self.params = params

        provider = self.providers[params.get('provider', 'gh')]
        try:
            spec = params['spec']
        except KeyError:
            spec = params['repo'] + '/' + params.get('branch', 'master')
        self.provider = provider(config = self.config, spec = spec)

        self.mounts = params.get('mounts', {})
        for (mount, path) in self.mounts.items():
            if not self.check_mount(path, stat):
                raise PermissionError(path)

    def check_mount(self, path, stat):
        if not any(path.startswith(a) for a in self.allowed_mounts):
            return False
        s = os.lstat(path)
        if not S_ISDIR(s.st_mode):
            return False
        need = S_IROTH | S_IXOTH
        if s.st_uid != stat.st_uid and s.st_gid != stat.st_gid or s.st_mode & need != need:
            return False
        return True

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
c.CuratedRepoProvider.allowed_mounts = ['/mnt/home/', '/mnt/ceph/']
c.LocalDirRepoProvider.allowed_paths = ['/mnt/home/']
c.LocalDirRepoProvider.required_marker = '.public_binder'
c.DockerRegistry.token_url = ''
c.KubeSpawner.cpu_limit = 0.5
c.KubeSpawner.mem_limit = '1G'
