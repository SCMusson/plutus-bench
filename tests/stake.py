import pathlib
from opshin import build
import pycardano
from pycardano import ChainContext
from pycardano.pool_params import PoolId
from pycardano.crypto.bech32 import decode

own_path = pathlib.Path(__file__)


def register_and_delegate(
    delegator_skey: pycardano.SigningKey,
    plutus_script: pycardano.PlutusV2Script,
    pool_id: PoolId,
    context: ChainContext,
):

    delegator_vkey_hash = delegator_skey.to_verification_key().hash()
    delegator_address = pycardano.Address(
        payment_part=delegator_vkey_hash, network=context.network
    )

    script_hash = pycardano.plutus_script_hash(plutus_script)
    stake_address = pycardano.Address(staking_part=script_hash, network=context.network)
    script_payment_address = pycardano.Address(
        payment_part=delegator_vkey_hash,
        staking_part=script_hash,
        network=context.network,
    )
    stake_credentials = pycardano.StakeCredential(script_hash)
    stake_registration = pycardano.StakeRegistration(stake_credentials)
    pool_keyhash = pycardano.VerificationKeyHash.from_primitive(
        bytes(decode(pool_id.value))
    )
    stake_delegation = pycardano.StakeDelegation(stake_credentials, pool_keyhash)

    builder = pycardano.TransactionBuilder(context)
    builder.add_input_address(delegator_address)
    builder.certificates = [stake_registration, stake_delegation]
    redeemer = pycardano.Redeemer(0)
    builder.add_certificate_script(plutus_script, redeemer=redeemer)
    tx = builder.build_and_sign(
        signing_keys=[delegator_skey],
        change_address=script_payment_address,
    )
    context.submit_tx(tx)
    return dict(
        stake_address=stake_address, script_payment_address=script_payment_address
    )


