import requests


class KubernetesClient:
    def __init__(self, base_url: str, token: str, ca_file: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = ca_file
        self.session.headers["Authorization"] = f"Bearer {token}"
        self.session.headers["User-Agent"] = (
            "os-deprecation (tools.os-deprecation@toolforge.org)"
            + f"python-requests/{requests.__version__}"
        )

    @staticmethod
    def create_inside_cluster():
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as token_file:
            token = token_file.read()
        return KubernetesClient(
            "https://kubernetes.default.svc",
            token,
            "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
        )

    def get(self, url, **kwargs):
        return self.session.get(f"{self.base_url}/{url.lstrip('/')}", **kwargs).json()
