import os
from binderhub.repoproviders import CuratedRepoProvider

c.BinderHub.hub_api_token = os.environ['JUPYTERHUB_API_TOKEN']
c.BinderHub.hub_url = os.environ['JUPYTERHUB_URL']
c.BinderHub.image_prefix = os.environ['DOCKER_REGISTRY'] + '/binder-'
c.BinderHub.use_registry = True
c.BinderHub.build_namespace = 'binder'
c.BinderHub.template_path = 'templates'
c.BinderHub.allowed_metrics_ips = ['10.0.0.0/8', '172.17.0.1']
c.BinderHub.repo_providers = {'user': CuratedRepoProvider}
c.CuratedRepoProvider.config_path = '/mnt/home/{0}/public_binder'
c.CuratedRepoProvider.allowed_mounts = ['/mnt/home/', '/mnt/ceph/']
c.CuratedRepoProvider.default_options = {
    'cpu_limit': 1,
    'mem_limit': '1G'
}
c.CuratedRepoProvider.allowed_options = []
c.LocalDirRepoProvider.allowed_paths = ['/mnt/home/']
c.LocalDirRepoProvider.required_marker = '.public_binder'
c.DockerRegistry.token_url = ''
c.BinderHub.per_repo_quota = 4
