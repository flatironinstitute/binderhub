import os
import string
import yaml
from traitlets import Dict, Unicode
from binderhub.app import BinderHub
from binderhub.repoproviders import RepoProvider, GitHubRepoProvider, GistRepoProvider, GitRepoProvider, GitLabRepoProvider

class CuratedRepoProvider(RepoProvider):
    """Curated meta-repo provider.

    This provider uses a meta-config that contains the specifications for other repositories.
    This can be used as a level of indirection to restrict what can be launched.
    """

    name = Unicode('Curated')

    config_file = Unicode(
        config=True,
        help="""
        Path to the yaml/json config file.
        {N} is expanded to the Nth component of the repo specification.""")

    providers = Dict(#BinderHub.repo_providers.default_value,
        {
            'gh': GitHubRepoProvider,
            'gist': GistRepoProvider,
            'git': GitRepoProvider,
            'gl': GitLabRepoProvider,
        },
        config=True,
        help="""Repo Providers to register""")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        safe_chars = frozenset(string.ascii_letters + string.digits + '-_/')
        if set(self.spec) - safe_chars:
            raise ValueError('Invalid characters in spec')

        spec = [x for x in self.spec.split('/') if x]
        path = self.config_file.format(*spec)
        with open(path) as f:
            params = yaml.safe_load(f)
        for p in spec:
            params = params[p]
        self.params = params

        provider = self.providers[params.get('provider', 'gh')]
        try:
            spec = params['spec']
        except KeyError:
            spec = params['repo'] + '/' + params.get('branch', 'master')
        self.provider = provider(config = self.config, spec = spec)

    def get_repo_url(self):
        return self.provider.get_repo_url()

    async def get_resolved_ref(self):
        return await self.provider.get_resolved_ref()

    def get_build_slug(self):
        return self.provider.get_build_slug()

    def get_launch_options(self):
        options = {'volumes': [], 'volume_mounts': []}
        for idx, (mount, path) in enumerate(self.params.get('mounts', {}).items(), 1):
            name = 'mount%d'%idx
            if not mount.startswith('/'):
                mount = '/home/jovyan/' + mount
            options['volumes'].append({'name': name, 'hostPath': {'path': path, 'type': 'Directory'}})
            options['volume_mounts'].append({'name': name, 'mountPath': mount, 'readOnly': True})
        return options

c.BinderHub.hub_api_token = os.environ['JUPYTERHUB_API_TOKEN']
c.BinderHub.hub_url = os.environ['JUPYTERHUB_URL']
c.BinderHub.image_prefix = os.environ['DOCKER_REGISTRY'] + '/binder-'
c.BinderHub.use_registry = True
c.BinderHub.build_namespace = 'binder'
c.BinderHub.template_path = 'templates'
c.BinderHub.repo_providers = {'fi': CuratedRepoProvider}
c.CuratedRepoProvider.config_file = '/user/{0}/.binders.yaml'
c.DockerRegistry.token_url = ''
c.KubeSpawner.cpu_limit = 0.5
c.KubeSpawner.mem_limit = '1G'
