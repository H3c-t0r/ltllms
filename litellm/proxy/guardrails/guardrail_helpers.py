from litellm._logging import verbose_proxy_logger
from litellm.proxy.guardrails.init_guardrails import guardrail_name_config_map
from litellm.proxy.proxy_server import UserAPIKeyAuth
from litellm.types.guardrails import *


async def should_proceed_based_on_metadata(data: dict, guardrail_name: str) -> bool:
    """
    checks if this guardrail should be applied to this call
    """
    if "metadata" in data and isinstance(data["metadata"], dict):
        if "guardrails" in data["metadata"]:
            # expect users to pass
            # guardrails: { prompt_injection: true, rail_2: false }
            request_guardrails = data["metadata"]["guardrails"]
            verbose_proxy_logger.debug(
                "Guardrails %s passed in request - checking which to apply",
                request_guardrails,
            )

            requested_callback_names = []

            # get guardrail configs from `init_guardrails.py`
            # for all requested guardrails -> get their associated callbacks
            for _guardrail_name, should_run in request_guardrails.items():
                if should_run is False:
                    verbose_proxy_logger.debug(
                        "Guardrail %s skipped because request set to False",
                        _guardrail_name,
                    )
                    continue

                # lookup the guardrail in guardrail_name_config_map
                guardrail_item: GuardrailItem = guardrail_name_config_map[
                    _guardrail_name
                ]

                guardrail_callbacks = guardrail_item.callbacks
                requested_callback_names.extend(guardrail_callbacks)

            verbose_proxy_logger.debug(
                "requested_callback_names %s", requested_callback_names
            )
            if guardrail_name in requested_callback_names:
                return True

            # Do no proceeed if - "metadata": { "guardrails": { "lakera_prompt_injection": false } }
            return False

    return True


async def should_proceed_based_on_api_key(
    user_api_key_dict: UserAPIKeyAuth, guardrail_name: str
) -> bool:
    """
    checks if this guardrail should be applied to this call
    """
    if user_api_key_dict.permissions is not None:
        # { prompt_injection: true, rail_2: false }
        verbose_proxy_logger.debug(
            "Guardrails valid for API Key= %s - checking which to apply",
            user_api_key_dict.permissions,
        )

        if not isinstance(user_api_key_dict.permissions, dict):
            verbose_proxy_logger.error(
                "API Key permissions must be a dict - %s running guardrail %s",
                user_api_key_dict,
                guardrail_name,
            )
            return True

        for _guardrail_name, should_run in user_api_key_dict.permissions.items():
            if should_run is False:
                verbose_proxy_logger.debug(
                    "Guardrail %s skipped because request set to False",
                    _guardrail_name,
                )
                continue

            # lookup the guardrail in guardrail_name_config_map
            guardrail_item: GuardrailItem = guardrail_name_config_map[_guardrail_name]

            guardrail_callbacks = guardrail_item.callbacks
            if guardrail_name in guardrail_callbacks:
                return True

        # Do not proceeed if - "metadata": { "guardrails": { "lakera_prompt_injection": false } }
        return False
    return True
