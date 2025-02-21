from typing import (
    Any,
    Dict,
)

from toolz import (
    assoc,
    dissoc,
)

from eth_account._utils.validation import (
    is_rlp_structured_access_list,
    is_rpc_structured_access_list,
    is_rlp_structured_authorisation_list,
    is_rpc_structured_authorisation_list
)
from eth_account.types import (
    AccessList,
    RLPStructuredAccessList,
    AuthorisationList,
    RLPStructuredAuthorisationList,
    TransactionDictType,
)


def normalize_transaction_dict(txn_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a transaction dictionary.
    """
    # convert all lists to tuples recursively
    for key, value in txn_dict.items():
        if isinstance(value, (list, tuple)):
            txn_dict[key] = tuple(
                normalize_transaction_dict(item) if isinstance(item, dict) else item
                for item in value
            )

        elif isinstance(value, dict):
            txn_dict[key] = normalize_transaction_dict(value)

    return txn_dict


def set_transaction_type_if_needed(
    transaction_dict: TransactionDictType,
) -> TransactionDictType:
    if "type" not in transaction_dict:
        if all(
            type_1_arg in transaction_dict for type_1_arg in ("gasPrice", "accessList")
        ):
            # access list txn - type 1
            transaction_dict = assoc(transaction_dict, "type", "0x1")
        elif any(
            type_2_arg in transaction_dict
            for type_2_arg in ("maxFeePerGas", "maxPriorityFeePerGas")
        ):
            if any(
                type_3_arg in transaction_dict
                for type_3_arg in ("maxFeePerBlobGas", "blobVersionedHashes")
            ):
                # blob txn - type 3
                transaction_dict = assoc(transaction_dict, "type", "0x3")
            elif "authorisationList" in transaction_dict:
                # set code txn - type 4
                transaction_dict = assoc(transaction_dict, "type", "0x4")                
            else:
                # dynamic fee txn - type 2
                transaction_dict = assoc(transaction_dict, "type", "0x2")
    return transaction_dict


# JSON-RPC to rlp transaction structure
def transaction_rpc_to_rlp_structure(dictionary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a JSON-RPC-structured transaction to an rlp-structured transaction.
    """
    access_list = dictionary.get("accessList")
    authorisation_list = dictionary.get("authorisationList")
    if access_list:
        dictionary = dissoc(dictionary, "accessList")
        rlp_structured_access_list = _access_list_rpc_to_rlp_structure(access_list)
        dictionary = assoc(dictionary, "accessList", rlp_structured_access_list)
        access_list = dictionary.get("accessList")
    if authorisation_list:
        dictionary = dissoc(dictionary, "authorisationList")
        rlp_structured_authorisation_list = _authorisation_list_rpc_to_rlp_structure(
            authorisation_list
        )
        dictionary = assoc(
            dictionary, "authorisationList", rlp_structured_authorisation_list
        )
        authorisation_list = dictionary.get("authorisationList")
    return dictionary


def _access_list_rpc_to_rlp_structure(
    access_list: AccessList,
) -> RLPStructuredAccessList:
    if not is_rpc_structured_access_list(access_list):
        raise ValueError(
            "provided object not formatted as JSON-RPC-structured access list"
        )

    # flatten each dict into a tuple of its values
    return tuple(
        (
            d["address"],  # value of address
            tuple(_ for _ in d["storageKeys"]),  # tuple of storage key values
        )
        for d in access_list
    )

def _authorisation_list_rpc_to_rlp_structure(
    authorisation_list: AuthorisationList,
) -> RLPStructuredAuthorisationList:
    if not is_rpc_structured_authorisation_list(authorisation_list):
        raise ValueError(
            "provided object not formatted as JSON-RPC-structured authorisation list"
        )
    # flatten each dict into a tuple of its values
    return tuple(
        (
            d["chainId"],
            d["address"],
            d["nonce"],
            d["yParity"],
            d["signerR"],
            d["signerS"],
        )
        for d in authorisation_list
    )

# rlp to JSON-RPC transaction structure
def transaction_rlp_to_rpc_structure(dictionary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert an rlp-structured transaction to a JSON-RPC-structured transaction.
    """
    access_list = dictionary.get("accessList")
    authorisation_list = dictionary.get("authorisationList")
    if access_list:
        dictionary = dissoc(dictionary, "accessList")
        rpc_structured_access_list = _access_list_rlp_to_rpc_structure(access_list)
        dictionary = assoc(dictionary, "accessList", rpc_structured_access_list)
    if authorisation_list:
        dictionary = dissoc(dictionary, "authorisationList")    # remove the access list from the dictionary
        rpc_structured_authorisation_list = _authorisation_list_rlp_to_rpc_structure(authorisation_list)
        dictionary = assoc(dictionary, "authorisationList", rpc_structured_authorisation_list)  # add the access list back to the dictionary
    return dictionary


def _access_list_rlp_to_rpc_structure(
    access_list: RLPStructuredAccessList,
) -> AccessList:
    if not is_rlp_structured_access_list(access_list):
        raise ValueError("provided object not formatted as rlp-structured access list")

    # build a dictionary with appropriate keys for each tuple
    return tuple({"address": t[0], "storageKeys": t[1]} for t in access_list)

def _authorisation_list_rlp_to_rpc_structure(
    authorisation_list: RLPStructuredAuthorisationList,
) -> AuthorisationList:
    if not is_rlp_structured_authorisation_list(authorisation_list):
        raise ValueError("provided object not formatted as rlp-structured authorisation list")
    # build a dictionary with appropriate keys for each tuple
    return tuple({  "chainId": t[0], 
                    "address": t[1],
                    "nonce": t[2],
                    "yParity": t[3],
                    "signerR": t[4],
                    "signerS": t[5]
                  } for t in authorisation_list)