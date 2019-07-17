import os
from binderhub.repoproviders import CuratedRepoProvider

c.BinderHub.auth_enabled = 'JUPYTERHUB_OAUTH_CALLBACK_URL' in os.environ
c.BinderHub.hub_api_token = os.environ['JUPYTERHUB_API_TOKEN']
c.BinderHub.hub_url = os.environ['JUPYTERHUB_URL']
c.HubOAuth.hub_host = os.environ['JUPYTERHUB_HOST']
registry = os.environ.get('DOCKER_REGISTRY')
if registry:
    c.BinderHub.image_prefix = registry + '/binder-'
    c.BinderHub.use_registry = True
    c.DockerRegistry.token_url = ''
else:
    c.BinderHub.image_prefix = 'binder-'
    c.BinderHub.use_registry = False
c.BinderHub.build_namespace = 'binder'
c.BinderHub.template_path = 'templates'
c.BinderHub.allowed_metrics_ips = ['10.0.0.0/8', '172.17.0.1']
c.BinderHub.repo_providers = {'user': CuratedRepoProvider}
c.CuratedRepoProvider.config_path = '/mnt/home/{0}/public_binder'
c.CuratedRepoProvider.dir_config = '.public_binder'
c.LocalDirRepoProvider.required_marker = '.public_binder'
c.LocalDirRepoProvider.allowed_paths = ['/mnt/home/']
c.CuratedRepoProvider.allowed_mounts = ['/mnt/home/', '/mnt/ceph/']
c.CuratedRepoProvider.default_options = {
    'cpu_guarantee': 1,
    'cpu_limit': 2,
    'mem_guarantee': '10G',
    'mem_limit': '20G',
}
c.CuratedRepoProvider.allowed_options = list(c.CuratedRepoProvider.default_options.keys())
c.CuratedRepoProvider.user_mount = 'home'
