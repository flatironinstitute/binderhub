import os
from binderhub.repoproviders import CuratedRepoProvider

c.BinderHub.hub_api_token = os.environ['JUPYTERHUB_API_TOKEN']
c.BinderHub.hub_url = os.environ['JUPYTERHUB_URL']
c.BinderHub.image_prefix = os.environ['DOCKER_REGISTRY'] + '/binder-'
c.BinderHub.use_registry = True
c.BinderHub.build_namespace = 'binder'
c.BinderHub.template_path = 'templates'
c.BinderHub.repo_providers = {'user': CuratedRepoProvider}
c.CuratedRepoProvider.config_path = '/mnt/home/{0}/public_binder'
c.CuratedRepoProvider.allowed_mounts = ['/mnt/home/', '/mnt/ceph/']
c.LocalDirRepoProvider.allowed_paths = ['/mnt/home/']
c.LocalDirRepoProvider.required_marker = '.public_binder'
c.DockerRegistry.token_url = ''
c.KubeSpawner.cpu_limit = 0.5
c.KubeSpawner.mem_limit = '1G'
