from ipaddress import IPv4Interface
from typing import Any, Dict, Mapping, Optional, Tuple, TypeAlias

from monkeytypes import (
    MachineID,
    MutableInfectionMonkeyBaseModel,
    NetworkService,
    OperatingSystem,
    SocketAddress,
)
from pydantic import Field, field_serializer, field_validator

from common.types import HardwareID

NetworkServices: TypeAlias = Dict[SocketAddress, NetworkService]


class Machine(MutableInfectionMonkeyBaseModel):
    """Represents machines, VMs, or other network nodes discovered by Infection Monkey"""

    @field_validator("network_services", mode="before")
    @classmethod
    def _socketaddress_from_string(cls, v: Any) -> Any:
        if not isinstance(v, Mapping):
            # Let pydantic's type validation handle this
            return v

        new_network_services = {}
        for addr, service in v.items():
            if isinstance(addr, SocketAddress):
                new_network_services[addr] = service
            else:
                new_network_services[SocketAddress.from_string(addr)] = service

        return new_network_services

    id: MachineID = Field(..., frozen=True)
    """Uniquely identifies the machine within the island"""

    hardware_id: Optional[HardwareID] = Field(default=None)
    """An identifier generated by the agent that uniquely identifies a machine"""

    island: bool = Field(default=False, frozen=True)
    """Whether or not the machine is an island (C&C server)"""

    network_interfaces: Tuple[IPv4Interface, ...] = tuple()
    """The machine's networking interfaces"""

    operating_system: Optional[OperatingSystem] = Field(default=None)
    """The operating system the machine is running"""

    operating_system_version: str = ""
    """The specific version of the operating system the machine is running"""

    hostname: str = ""
    """The hostname of the machine"""

    network_services: NetworkServices = Field(default_factory=dict)
    """All network services found running on the machine"""

    @field_serializer("network_services", when_used="json")
    def dump_network_services(self, value: Any):
        return {str(addr): val for addr, val in value.items()}

    def __hash__(self):
        return self.id
