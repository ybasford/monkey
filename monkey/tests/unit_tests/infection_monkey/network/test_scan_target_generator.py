from itertools import chain

import pytest

from infection_monkey.network.scan_target_generator import (
    NetworkInterface,
    compile_scan_target_list,
)


def compile_ranges_only(ranges):
    return compile_scan_target_list(
        local_network_interfaces=[],
        ranges_to_scan=ranges,
        inaccessible_subnets=[],
        blocklisted_ips=[],
        enable_local_network_scan=False,
    )


def test_single_subnet():
    scan_targets = compile_ranges_only(["10.0.0.0/24"])

    assert len(scan_targets) == 255

    for i in range(0, 255):
        assert f"10.0.0.{i}" in scan_targets


@pytest.mark.parametrize("single_ip", ["10.0.0.2", "10.0.0.2/32", "10.0.0.2-10.0.0.2"])
def test_single_ip(single_ip):
    print(single_ip)
    scan_targets = compile_ranges_only([single_ip])

    assert len(scan_targets) == 1
    assert "10.0.0.2" in scan_targets
    assert "10.0.0.2" == scan_targets[0]


def test_multiple_subnet():
    scan_targets = compile_ranges_only(["10.0.0.0/24", "192.168.56.8/29"])

    assert len(scan_targets) == 262

    for i in range(0, 255):
        assert f"10.0.0.{i}" in scan_targets

    for i in range(8, 15):
        assert f"192.168.56.{i}" in scan_targets


def test_middle_of_range_subnet():
    scan_targets = compile_ranges_only(["192.168.56.4/29"])

    assert len(scan_targets) == 7

    for i in range(0, 7):
        assert f"192.168.56.{i}" in scan_targets


@pytest.mark.parametrize(
    "ip_range",
    ["192.168.56.25-192.168.56.33", "192.168.56.25 - 192.168.56.33", "192.168.56.33-192.168.56.25"],
)
def test_ip_range(ip_range):
    scan_targets = compile_ranges_only([ip_range])

    assert len(scan_targets) == 9

    for i in range(25, 34):
        assert f"192.168.56.{i}" in scan_targets


def test_no_duplicates():
    scan_targets = compile_ranges_only(["192.168.56.0/29", "192.168.56.2", "192.168.56.4"])

    assert len(scan_targets) == 7

    for i in range(0, 7):
        assert f"192.168.56.{i}" in scan_targets


def test_blocklisted_ips():
    blocklisted_ips = ["10.0.0.5", "10.0.0.32", "10.0.0.119", "192.168.1.33"]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=[],
        ranges_to_scan=["10.0.0.0/24"],
        inaccessible_subnets=[],
        blocklisted_ips=blocklisted_ips,
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 252
    for blocked_ip in blocklisted_ips:
        assert blocked_ip not in scan_targets


@pytest.mark.parametrize("ranges_to_scan", [["10.0.0.5"], []])
def test_only_ip_blocklisted(ranges_to_scan):
    blocklisted_ips = ["10.0.0.5"]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=[],
        ranges_to_scan=ranges_to_scan,
        inaccessible_subnets=[],
        blocklisted_ips=blocklisted_ips,
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 0


def test_local_network_interface_ips_removed_from_targets():
    local_network_interfaces = [
        NetworkInterface("10.0.0.5", "/24"),
        NetworkInterface("10.0.0.32", "/24"),
        NetworkInterface("10.0.0.119", "/24"),
        NetworkInterface("192.168.1.33", "/24"),
    ]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=["10.0.0.0/24"],
        inaccessible_subnets=[],
        blocklisted_ips=[],
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 252
    for interface in local_network_interfaces:
        assert interface.address not in scan_targets


@pytest.mark.parametrize("ranges_to_scan", [["10.0.0.5"], []])
def test_only_scan_ip_is_local(ranges_to_scan):
    local_network_interfaces = [
        NetworkInterface("10.0.0.5", "/24"),
        NetworkInterface("10.0.0.32", "/24"),
        NetworkInterface("10.0.0.119", "/24"),
        NetworkInterface("192.168.1.33", "/24"),
    ]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=ranges_to_scan,
        inaccessible_subnets=[],
        blocklisted_ips=[],
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 0


def test_local_network_interface_ips_and_blocked_ips_removed_from_targets():
    local_network_interfaces = [
        NetworkInterface("10.0.0.5", "/24"),
        NetworkInterface("10.0.0.32", "/24"),
        NetworkInterface("10.0.0.119", "/24"),
        NetworkInterface("192.168.1.33", "/24"),
    ]
    blocked_ips = ["10.0.0.63", "192.168.1.77", "0.0.0.0"]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=["10.0.0.0/24", "192.168.1.0/24"],
        inaccessible_subnets=[],
        blocklisted_ips=blocked_ips,
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == (2 * (256 - 1)) - len(local_network_interfaces) - (
        len(blocked_ips) - 1
    )

    for interface in local_network_interfaces:
        assert interface.address not in scan_targets

    for ip in blocked_ips:
        assert ip not in scan_targets


def test_local_subnet_added():
    local_network_interfaces = [NetworkInterface("10.0.0.5", "/24")]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=[],
        inaccessible_subnets=[],
        blocklisted_ips=[],
        enable_local_network_scan=True,
    )

    assert len(scan_targets) == 254

    for ip in chain(range(0, 5), range(6, 255)):
        assert f"10.0.0.{ip} in scan_targets"


def test_multiple_local_subnets_added():
    local_network_interfaces = [
        NetworkInterface("10.0.0.5", "/24"),
        NetworkInterface("172.33.66.99", "/24"),
    ]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=[],
        inaccessible_subnets=[],
        blocklisted_ips=[],
        enable_local_network_scan=True,
    )

    assert len(scan_targets) == 2 * (255 - 1)

    for ip in chain(range(0, 5), range(6, 255)):
        assert f"10.0.0.{ip} in scan_targets"

    for ip in chain(range(0, 99), range(100, 255)):
        assert f"172.33.66.{ip} in scan_targets"


def test_blocklisted_ips_missing_from_local_subnets():
    local_network_interfaces = [
        NetworkInterface("10.0.0.5", "/24"),
        NetworkInterface("172.33.66.99", "/24"),
    ]
    blocklisted_ips = ["10.0.0.12", "10.0.0.13", "172.33.66.25"]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=[],
        inaccessible_subnets=[],
        blocklisted_ips=blocklisted_ips,
        enable_local_network_scan=True,
    )

    assert len(scan_targets) == 2 * (255 - 1) - len(blocklisted_ips)

    for ip in blocklisted_ips:
        assert ip not in scan_targets


def test_local_subnets_and_ranges_added():
    local_network_interfaces = [NetworkInterface("10.0.0.5", "/24")]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=["172.33.66.40/30"],
        inaccessible_subnets=[],
        blocklisted_ips=[],
        enable_local_network_scan=True,
    )

    assert len(scan_targets) == 254 + 3

    for ip in range(0, 5):
        assert f"10.0.0.{ip} in scan_targets"
    for ip in range(6, 255):
        assert f"10.0.0.{ip} in scan_targets"

    for ip in range(40, 43):
        assert f"172.33.66.{ip} in scan_targets"


def test_local_network_interfaces_specified_but_disabled():
    local_network_interfaces = [NetworkInterface("10.0.0.5", "/24")]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=["172.33.66.40/30"],
        inaccessible_subnets=[],
        blocklisted_ips=[],
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 3

    for ip in range(40, 43):
        assert f"172.33.66.{ip} in scan_targets"


def test_local_network_interfaces_subnet_masks():
    local_network_interfaces = [
        NetworkInterface("172.60.145.109", "/30"),
        NetworkInterface("172.60.145.144", "/30"),
    ]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=[],
        inaccessible_subnets=[],
        blocklisted_ips=[],
        enable_local_network_scan=True,
    )

    assert len(scan_targets) == 4

    for ip in [108, 110, 145, 146]:
        assert f"172.60.145.{ip}" in scan_targets


def test_segmentation_targets():
    local_network_interfaces = [NetworkInterface("172.60.145.109", "/24")]

    inaccessible_subnets = ["172.60.145.108/30", "172.60.145.144/30"]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=[],
        inaccessible_subnets=inaccessible_subnets,
        blocklisted_ips=[],
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 3

    for ip in [144, 145, 146]:
        assert f"172.60.145.{ip}" in scan_targets


def test_segmentation_clash_with_blocked():
    local_network_interfaces = [
        NetworkInterface("172.60.145.109", "/30"),
    ]

    inaccessible_subnets = ["172.60.145.108/30", "172.60.145.149/30"]

    blocked = ["172.60.145.148", "172.60.145.149", "172.60.145.150"]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=[],
        inaccessible_subnets=inaccessible_subnets,
        blocklisted_ips=blocked,
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 0


def test_segmentation_clash_with_targets():
    local_network_interfaces = [
        NetworkInterface("172.60.145.109", "/30"),
    ]

    inaccessible_subnets = ["172.60.145.108/30", "172.60.145.149/30"]

    targets = ["172.60.145.149", "172.60.145.150"]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=targets,
        inaccessible_subnets=inaccessible_subnets,
        blocklisted_ips=[],
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 3

    for ip in [148, 149, 150]:
        assert f"172.60.145.{ip}" in scan_targets


def test_segmentation_one_network():
    local_network_interfaces = [
        NetworkInterface("172.60.145.109", "/30"),
    ]

    inaccessible_subnets = ["172.60.145.1/24"]

    targets = ["172.60.145.149/30"]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=targets,
        inaccessible_subnets=inaccessible_subnets,
        blocklisted_ips=[],
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 3


def test_segmentation_inaccessible_networks():
    local_network_interfaces = [
        NetworkInterface("172.60.1.1", "/24"),
        NetworkInterface("172.60.2.1", "/24"),
    ]

    inaccessible_subnets = ["172.60.144.1/24", "172.60.146.1/24"]

    scan_targets = compile_scan_target_list(
        local_network_interfaces=local_network_interfaces,
        ranges_to_scan=[],
        inaccessible_subnets=inaccessible_subnets,
        blocklisted_ips=[],
        enable_local_network_scan=False,
    )

    assert len(scan_targets) == 0
