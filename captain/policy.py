from pathlib import Path
import ipaddress


class PolicyError(ValueError):
    pass


class Policy:
    def __init__(self, config):
        self.workspace = Path(config.workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.networks = [ipaddress.ip_network(n, strict=True) for n in config.allowed_networks]

    def host(self, value):
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            raise PolicyError("Use a literal authorized IP address, not a hostname or range.")
        if not any(address in net for net in self.networks):
            raise PolicyError("That target is outside the configured engagement scope.")
        return str(address)

    def path(self, value):
        candidate = (self.workspace / value).resolve()
        if not candidate.is_relative_to(self.workspace) or candidate == self.workspace:
            raise PolicyError("File access is restricted to the configured workspace.")
        return candidate
