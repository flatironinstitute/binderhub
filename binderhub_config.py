import os
import string
import escapism
from traitlets import Dict, Unicode
from binderhub.repoproviders import RepoProvider, GitHubRepoProvider

class CuratedRepoProvider(RepoProvider):
    """Curated meta-repo provider.

    This provider requires a meta-repo that contains the specifications for other repositories.
    Specs match the name of a file in this repository.
    """

    name = Unicode('Curated')

    repos = Dict(
        config=True,
        help="""The meta configuration to use.""")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        path = self.spec.split('/')
        params = self.repos
        for p in path:
            params = params[p]
        self.params = params
        self.provider = params['provider'](config = self.config, **params)

    def get_repo_url(self):
        return self.provider.get_repo_url()

    async def get_resolved_ref(self):
        return await self.provider.get_resolved_ref()

    def get_build_slug(self):
        return self.provider.get_build_slug()

    def get_launch_options(self):
        safe_chars = set(string.ascii_letters + string.digits)
        options = {'volumes': [], 'volume_mounts': []}
        for mount, path in self.params.get('mounts', {}).items():
            name = escapism.escape(mount, safe=safe_chars, escape_char='-')
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
c.CuratedRepoProvider.repos = {
    'triqstest': {
        'provider': GitHubRepoProvider,
        'spec': 'TRIQS/binder/master',
        'mounts': {
            'stuff': '/simons/scratch/dylan/gaea'
        }
    }
}
c.DockerRegistry.token_url = ''
