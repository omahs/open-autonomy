# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
"""Constants"""
import os


import os


DEFAULT_BUILD_FOLDER = "abci_build"

DEFAULT_IMAGE_VERSION = "0.1.0"
IMAGE_VERSION = os.environ.get("VERSION", DEFAULT_IMAGE_VERSION)
TENDERMINT_IMAGE_VERSION = os.environ.get(
    "TENDERMINT_IMAGE_VERSION", DEFAULT_IMAGE_VERSION
)
HARDHAT_IMAGE_VERSION = os.environ.get("HARDHAT_IMAGE_VERSION", DEFAULT_IMAGE_VERSION)
OPEN_AEA_IMAGE_NAME = "valory/consensus-algorithms-open-aea"
TENDERMINT_IMAGE_NAME = "valory/consensus-algorithms-tendermint"
HARDHAT_IMAGE_NAME = "valory/consensus-algorithms-hardhat"

DEPLOYMENT_KEY_DIRECTORY = "agent_keys"
DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA = "agent_{agent_n}"

DEFAULT_ENCODING = "utf-8"

KEY_SCHEMA_ADDRESS = "address"
KEY_SCHEMA_ENCRYPTED_KEY = "encrypted_key"
KEY_SCHEMA_UNENCRYPTED_KEY = "private_key"
