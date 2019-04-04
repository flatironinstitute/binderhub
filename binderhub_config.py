import os
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
        return self.params.get('options')

c.BinderHub.hub_api_token = os.environ['JUPYTERHUB_API_TOKEN']
c.BinderHub.hub_url = os.environ['JUPYTERHUB_URL']
c.BinderHub.image_prefix = os.environ['DOCKER_REGISTRY'] + '/binder-'
c.BinderHub.use_registry = True
c.BinderHub.build_namespace = 'binder'
c.BinderHub.repo_providers = {'fi': CuratedRepoProvider}
c.CuratedRepoProvider.repos = {
    'triqstest': {
        'provider': GitHubRepoProvider,
        'spec': 'TRIQS/binder/master',
        'options': {
            'singleuser_extra_labels': {'testlabel':'testtriqs'}
        }
    }
}
c.DockerRegistry.token_url = ''
