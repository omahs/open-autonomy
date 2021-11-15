# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Integration tests for the valory/counter skill."""
import base64
import json
import logging
import random
import struct
import time
from pathlib import Path

import pytest
import requests
from aea.test_tools.test_cases import AEATestCaseEmpty, AEATestCaseMany

from tests.fixture_helpers import UseTendermint
from tests.helpers.constants import DEFAULT_REQUESTS_TIMEOUT
from tests.helpers.tendermint_utils import (
    BaseTendermintTestClass,
    TendermintLocalNetworkBuilder,
)


class BaseTestABCICounterSkill:
    """Base test class."""

    def _send_tx_to_node(
        self, node_address: str, value: int, expected_status_code: int
    ) -> None:
        """
        Send a transaction to a certain node.

        :param node_address: the node address
        :param value: the value to propose in the tx
        :param expected_status_code: the expected status code
        """
        # at least two hex digits
        tx_arg = "0x{:02x}".format(value)
        result = requests.get(
            node_address + "/broadcast_tx_commit",
            params=dict(tx=tx_arg),
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
        assert result.status_code == expected_status_code

    def _query_node(self, node_address: str, expected_value: int) -> None:
        """
        Send a query to a node about the state of the replicated counter.

        :param node_address: the node address
        :param expected_value: the expected value of the counter.
        """
        result = requests.get(
            node_address + "/abci_query",
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
        assert result.status_code == 200
        counter_value_base64 = result.json()["result"]["response"]["value"].encode(
            "ascii"
        )
        counter_value_bytes = base64.b64decode(counter_value_base64)
        counter_value, *_ = struct.unpack(">I", counter_value_bytes)
        assert counter_value == expected_value


@pytest.mark.integration
class TestABCICounterSkill(AEATestCaseEmpty, UseTendermint):
    """Test that the ABCI counter skill works together with Tendermint."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "DEBUG"]

    def test_run(self) -> None:
        """Run the ABCI skill."""
        self.generate_private_key("ethereum")
        self.add_private_key("ethereum", "ethereum_private_key.txt")
        self.set_config("agent.default_ledger", "ethereum")
        self.set_config("agent.required_ledgers", '["ethereum"]', type_="list")
        self.add_item("skill", "valory/counter:0.1.0")
        self.set_config(
            "vendor.valory.connections.abci.config.target_skill_id",
            "valory/counter:0.1.0",
        )
        self.set_config("vendor.valory.connections.abci.config.use_tendermint", False)

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        time.sleep(2.0)

        check_strings = (
            "ABCI Handler: setup method called.",
            "Received ABCI request of type info",
            "Received ABCI request of type flush",
            "Received ABCI request of type begin_block",
            "Received ABCI request of type commit",
            "Received ABCI request of type end_block",
        )
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        assert (
            self.is_successfully_terminated()
        ), "ABCI agent wasn't successfully terminated."


class TestABCICounterSkillMany(
    AEATestCaseMany, BaseTendermintTestClass, BaseTestABCICounterSkill
):
    """Test that the ABCI counter skill works together with Tendermint."""

    IS_LOCAL = True
    capture_log = True
    NB_AGENTS = 4
    NB_TX = 15

    def test_run(self) -> None:
        """Run the ABCI skill."""
        self.agent_names = [f"agent_{i:05d}" for i in range(self.NB_AGENTS)]
        processes = []
        self.create_agents(*self.agent_names, is_local=self.IS_LOCAL)
        self.tendermint_net_builder = TendermintLocalNetworkBuilder(
            self.NB_AGENTS, Path(self.t)
        )

        for agent_id, agent_name in enumerate(self.agent_names):
            logging.debug(f"Processing agent {agent_name}...")
            node = self.tendermint_net_builder.nodes[agent_id]
            self.set_agent_context(agent_name)
            self.generate_private_key("ethereum")
            self.add_private_key("ethereum", "ethereum_private_key.txt")
            self.set_config("agent.default_ledger", "ethereum")
            self.set_config("agent.required_ledgers", '["ethereum"]', type_="list")
            self.add_item("skill", "valory/counter:0.1.0")
            self.set_config(
                "vendor.valory.connections.abci.config.target_skill_id",
                "valory/counter:0.1.0",
            )
            # each agent has its Tendermint node instance
            self.set_config(
                "vendor.valory.connections.abci.config.use_tendermint", True
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.consensus_create_empty_blocks",
                True,
            )

            self.set_config(
                "vendor.valory.connections.abci.config.port",
                node.abci_port,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.rpc_laddr",
                node.rpc_laddr,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.p2p_laddr",
                node.p2p_laddr,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.home",
                str(node.home),
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.p2p_seeds",
                json.dumps(self.tendermint_net_builder.get_p2p_seeds()),
                "list",
            )
            process = self.run_agent()
            processes.append(process)

        logging.info("Waiting Tendermint nodes to be up")
        self.health_check(self.tendermint_net_builder)

        # start test of the ABCI app
        # check that the initial counter state is 0
        self._query_agents(0)
        # send transactions to each node, randomly
        for tx_number in range(self.NB_TX):
            time.sleep(0.5)
            agent_id = random.randint(0, self.NB_AGENTS - 1)  # nosec
            new_value = tx_number + 1
            self._send_tx(new_value, agent_id, 200)
        # wait synchronization
        time.sleep(2.0)
        # check that the final counter state is N
        self._query_agents(self.NB_TX)
        # end test of the ABCI app

        check_strings = (*[f"The new count is: {x + 1}" for x in range(self.NB_TX)],)

        # check that *each* AEA prints these messages
        for process in processes:
            missing_strings = self.missing_from_output(process, check_strings)
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in agent output.".format(missing_strings)

            assert self.is_successfully_terminated(
                process
            ), "ABCI agent wasn't successfully terminated."

    def _query_agents(self, expected_value: int) -> None:
        """
        Send queries to each agent about the state of the replicated counter.

        :param expected_value: the expected value of the counter.
        """
        for agent_id in range(self.NB_AGENTS):
            self._query_agent(expected_value, agent_id)

    def _send_tx(self, value: int, agent_id: int, expected_status_code: int) -> None:
        """
        Send a transaction to a certain agent.

        :param value: the value to propose in the tx
        :param agent_id: the agent id
        :param expected_status_code: the expected status code
        """
        node = self.tendermint_net_builder.nodes[agent_id]
        self._send_tx_to_node(
            node.get_http_addr("localhost"), value, expected_status_code
        )

    def _query_agent(self, expected_value: int, agent_id: int) -> None:
        """
        Send a query to the ith agent about the state of the replicated counter.

        :param expected_value: the expected value of the counter.
        :param agent_id: the agent to be queried
        """
        node = self.tendermint_net_builder.nodes[agent_id]
        result = requests.get(
            node.get_http_addr("localhost") + "/abci_query",
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
        assert result.status_code == 200
        counter_value_base64 = result.json()["result"]["response"]["value"].encode(
            "ascii"
        )
        counter_value_bytes = base64.b64decode(counter_value_base64)
        counter_value, *_ = struct.unpack(">I", counter_value_bytes)
        assert counter_value == expected_value


class TestABCICounterCrashFailureRestart(
    AEATestCaseEmpty, BaseTendermintTestClass, BaseTestABCICounterSkill
):
    """Test that restarting the agent with the same Tendermint node will restore the state."""

    NB_TX = 5

    def test_run(self) -> None:
        """Run the test."""
        self.generate_private_key("ethereum")
        self.add_private_key("ethereum", "ethereum_private_key.txt")
        self.set_config("agent.default_ledger", "ethereum")
        self.set_config("agent.required_ledgers", '["ethereum"]', type_="list")
        self.add_item("skill", "valory/counter:0.1.0")
        self.set_config(
            "vendor.valory.connections.abci.config.target_skill_id",
            "valory/counter:0.1.0",
        )
        self.set_config("vendor.valory.connections.abci.config.use_tendermint", True)
        self.set_config(
            "vendor.valory.connections.abci.config.tendermint_config.home",
            str(self.t / "tendermint_home"),
        )

        node_address = "http://localhost:26657"

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        time.sleep(5.0)

        for tx_number in range(self.NB_TX):
            time.sleep(2.0)
            new_value = tx_number + 1
            self._send_tx_to_node(node_address, new_value, 200)
        # wait synchronization
        time.sleep(5.0)

        # check that the final counter state is N
        self._query_node(node_address, self.NB_TX)

        check_strings = (*[f"The new count is: {x + 1}" for x in range(self.NB_TX)],)
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        # Run it again
        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        # give time to synchronize
        time.sleep(5.0)

        self._query_node(node_address, self.NB_TX)

        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)
