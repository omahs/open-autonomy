<a id="autonomy.cli.helpers.deployment"></a>

# autonomy.cli.helpers.deployment

Deployment helpers.

<a id="autonomy.cli.helpers.deployment.run_deployment"></a>

#### run`_`deployment

```python
def run_deployment(build_dir: Path,
                   no_recreate: bool = False,
                   remove_orphans: bool = False) -> None
```

Run deployment.

<a id="autonomy.cli.helpers.deployment.build_deployment"></a>

#### build`_`deployment

```python
def build_deployment(keys_file: Path,
                     build_dir: Path,
                     deployment_type: str,
                     dev_mode: bool,
                     number_of_agents: Optional[int] = None,
                     password: Optional[str] = None,
                     packages_dir: Optional[Path] = None,
                     open_aea_dir: Optional[Path] = None,
                     open_autonomy_dir: Optional[Path] = None,
                     agent_instances: Optional[List[str]] = None,
                     multisig_address: Optional[str] = None,
                     consensus_threshold: Optional[int] = None,
                     log_level: str = INFO,
                     apply_environment_variables: bool = False,
                     image_version: Optional[str] = None,
                     use_hardhat: bool = False,
                     use_acn: bool = False,
                     use_tm_testnet_setup: bool = False,
                     image_author: Optional[str] = None) -> None
```

Build deployment.

<a id="autonomy.cli.helpers.deployment.build_and_deploy_from_token"></a>

#### build`_`and`_`deploy`_`from`_`token

```python
def build_and_deploy_from_token(token_id: int,
                                keys_file: Path,
                                chain_type: ChainType,
                                skip_image: bool,
                                n: Optional[int],
                                deployment_type: str,
                                aev: bool = False,
                                password: Optional[str] = None,
                                no_deploy: bool = False) -> None
```

Build and run deployment from tokenID.

