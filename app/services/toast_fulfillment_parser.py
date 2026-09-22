from app.services.toast_fulfillment import (
    ToastFulfillmentError,
    ToastOrderFulfillment,
    ToastSelectionFulfillment,
    aggregate_fulfillment_status,
    is_order_ready,
    normalize_fulfillment_status,
)


def parse_toast_order_fulfillment(
    payload: dict,
) -> ToastOrderFulfillment:
    if not isinstance(payload, dict):
        raise ToastFulfillmentError(
            "La respuesta de Toast debe ser un objeto."
        )

    order_guid = payload.get("guid")

    if not isinstance(order_guid, str):
        raise ToastFulfillmentError(
            "La respuesta de Toast no contiene order guid."
        )

    order_guid = order_guid.strip()

    if not order_guid:
        raise ToastFulfillmentError(
            "La respuesta de Toast no contiene order guid."
        )

    approval_status = payload.get(
        "approvalStatus"
    )

    if approval_status is not None:
        if not isinstance(approval_status, str):
            raise ToastFulfillmentError(
                "approvalStatus de Toast no es válido."
            )

        approval_status = (
            approval_status.strip().upper()
        )

        if not approval_status:
            approval_status = None

    checks = payload.get("checks")

    if not isinstance(checks, list):
        raise ToastFulfillmentError(
            "La respuesta de Toast no contiene checks válidos."
        )

    selections = []

    for check in checks:
        if not isinstance(check, dict):
            continue

        check_selections = check.get(
            "selections"
        )

        if not isinstance(
            check_selections,
            list,
        ):
            continue

        for selection in check_selections:
            if not isinstance(
                selection,
                dict,
            ):
                continue

            selection_guid = (
                selection.get("guid")
            )

            if not isinstance(
                selection_guid,
                str,
            ):
                raise ToastFulfillmentError(
                    "Selection de Toast sin guid válido."
                )

            selection_guid = (
                selection_guid.strip()
            )

            if not selection_guid:
                raise ToastFulfillmentError(
                    "Selection de Toast sin guid válido."
                )

            fulfillment_status = (
                selection.get(
                    "fulfillmentStatus"
                )
            )

            normalized_status = (
                normalize_fulfillment_status(
                    fulfillment_status
                )
            )

            selections.append(
                ToastSelectionFulfillment(
                    selection_guid=(
                        selection_guid
                    ),
                    fulfillment_status=(
                        normalized_status
                    ),
                )
            )

    if not selections:
        raise ToastFulfillmentError(
            "La orden de Toast no contiene selections "
            "con fulfillment."
        )

    statuses = tuple(
        selection.fulfillment_status
        for selection in selections
    )

    return ToastOrderFulfillment(
        order_guid=order_guid,
        approval_status=approval_status,
        fulfillment_status=(
            aggregate_fulfillment_status(
                statuses
            )
        ),
        selections=tuple(selections),
        ready=is_order_ready(
            statuses
        ),
    )


__all__ = [
    "parse_toast_order_fulfillment",
]
