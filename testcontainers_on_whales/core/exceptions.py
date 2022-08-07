class ContainerError(Exception):
    pass


class NetworkModeUnknownError(ContainerError):
    def __init__(self, network_mode: str) -> None:
        self.network_mode = network_mode
        super().__init__(f"Unknown network_mode={self.network_mode}")


class PortBindingNotFoundError(ContainerError):
    def __init__(self, port_name: str) -> None:
        self.port_name = port_name
        super().__init__(f"PortBinding for port '{self.port_name}' not found")


class ContainerRuntimeError(Exception):
    pass


class ContainerRuntimeNotFoundError(ContainerRuntimeError):
    pass
