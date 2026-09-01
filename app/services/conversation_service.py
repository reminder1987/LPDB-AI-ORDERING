import json
import unicodedata

from dataclasses import dataclass, field

from app.core.database import SessionLocal
from app.core.tenant_context import TenantContext

from app.models.conversation_session_db import (
    ConversationSessionDB,
)

from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderModificationCreate,
)

from app.services.intent_service import (
    IntentItem,
    IntentModification,
    parse_customer_message,
)

from app.services.location_service import (
    location_service,
)

from app.services.order_service import (
    create_order,
)


# ============================================================
# HELPERS
# ============================================================


def _normalize(
    text: str,
) -> str:

    normalized = unicodedata.normalize(
        "NFD",
        text.strip(),
    )

    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )

    return normalized.upper()


def _is_yes(
    text: str,
) -> bool:

    return _normalize(text) in {
        "SI",
        "S",
        "YES",
        "Y",
    }


def _is_no(
    text: str,
) -> bool:

    return _normalize(text) in {
        "NO",
        "N",
    }


def _to_order_modification(
    modification: IntentModification,
) -> OrderModificationCreate:

    return OrderModificationCreate(
        type=modification.type,
        ingredient=modification.ingredient,
        new_base=modification.new_base,
    )


# ============================================================
# ESTADO DE CONVERSACIÓN
# ============================================================


@dataclass
class ConversationState:

    # --------------------------------------------------------
    # Estado general
    # --------------------------------------------------------

    status: str = "new"

    # --------------------------------------------------------
    # Productos pendientes
    # --------------------------------------------------------

    items: list[IntentItem] = field(
        default_factory=list,
    )

    # --------------------------------------------------------
    # Combo
    # --------------------------------------------------------

    combo_requested: bool = False

    combo_product: str | None = None

    beverage_required: bool = False

    beverage_product_id: int | None = None

    beverage_name: str | None = None

    # --------------------------------------------------------
    # Cliente
    # --------------------------------------------------------

    customer_id: int | None = None

    customer_name: str | None = None

    # --------------------------------------------------------
    # Sede
    # --------------------------------------------------------

    location_id: int | None = None


# ============================================================
# SERVICIO
# ============================================================


class ConversationService:

    def __init__(self):
        """
        El estado de conversación se almacena en PostgreSQL.

        La tabla conversation_sessions es la fuente de verdad.
        """

        pass

    # ========================================================
    # ESTADO PERSISTENTE
    # ========================================================

    def get_state(
        self,
        session_id: str,
        tenant_id: int,
    ) -> ConversationState:

        db = SessionLocal()

        try:

            session = (
                db.query(
                    ConversationSessionDB,
                )
                .filter(
                    ConversationSessionDB.session_id
                    == session_id,
                    ConversationSessionDB.tenant_id
                    == tenant_id,
                )
                .first()
            )

            if session is None:

                return ConversationState()

            return self._db_to_state(
                session,
            )

        finally:

            db.close()

    # --------------------------------------------------------

    def get_openai_response_id(
        self,
        session_id: str,
        tenant_id: int,
    ) -> str | None:
        """
        Recupera el último OpenAI response ID asociado
        a una sesión concreta dentro de un tenant.
        """

        db = SessionLocal()

        try:

            session = (
                db.query(
                    ConversationSessionDB,
                )
                .filter(
                    ConversationSessionDB.session_id
                    == session_id,
                    ConversationSessionDB.tenant_id
                    == tenant_id,
                )
                .first()
            )

            if session is None:

                return None

            return session.openai_response_id

        finally:

            db.close()

    # --------------------------------------------------------

    def save_openai_response_id(
        self,
        session_id: str,
        tenant_id: int,
        response_id: str | None,
    ) -> None:
        """
        Guarda el último OpenAI response ID de la conversación.

        La sesión siempre está aislada por tenant.
        """

        db = SessionLocal()

        try:

            session = (
                db.query(
                    ConversationSessionDB,
                )
                .filter(
                    ConversationSessionDB.session_id
                    == session_id,
                    ConversationSessionDB.tenant_id
                    == tenant_id,
                )
                .first()
            )

            if session is None:

                session = ConversationSessionDB(
                    session_id=session_id,
                    tenant_id=tenant_id,
                )

                db.add(session)

            session.openai_response_id = response_id

            db.commit()

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()

    # --------------------------------------------------------

    def _save_state(
        self,
        session_id: str,
        state: ConversationState,
        tenant_id: int,
    ) -> None:

        db = SessionLocal()

        try:

            session = (
                db.query(
                    ConversationSessionDB,
                )
                .filter(
                    ConversationSessionDB.session_id
                    == session_id,
                    ConversationSessionDB.tenant_id
                    == tenant_id,
                )
                .first()
            )

            if session is None:

                session = ConversationSessionDB(
                    session_id=session_id,
                    tenant_id=tenant_id,
                )

                db.add(session)

                # ------------------------------------------------
                # Materializamos la nueva sesión antes del commit.
                #
                # Esto garantiza que la instancia recién creada
                # quede registrada en la transacción actual antes
                # de continuar con la asignación del estado.
                # ------------------------------------------------

                db.flush()

            session.status = state.status

            session.customer_id = (
                state.customer_id
            )

            session.customer_name = (
                state.customer_name
            )

            session.location_id = (
                state.location_id
            )

            session.items_json = json.dumps(
                [
                    {
                        "product": item.product,
                        "quantity": item.quantity,
                        "modifications": [
                            {
                                "type": modification.type,
                                "ingredient": modification.ingredient,
                                "new_base": modification.new_base,
                            }
                            for modification
                            in item.modifications
                        ],
                    }
                    for item in state.items
                ],
                ensure_ascii=False,
            )

            session.combo_requested = (
                state.combo_requested
            )

            session.combo_product = (
                state.combo_product
            )

            session.beverage_required = (
                state.beverage_required
            )

            session.beverage_product_id = (
                state.beverage_product_id
            )

            session.beverage_name = (
                state.beverage_name
            )

            # ------------------------------------------------
            # Confirmamos explícitamente toda la persistencia.
            # ------------------------------------------------

            db.commit()

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()

    # --------------------------------------------------------

    def _clear_state(
        self,
        session_id: str,
        tenant_id: int,
    ) -> None:

        db = SessionLocal()

        try:

            session = (
                db.query(
                    ConversationSessionDB,
                )
                .filter(
                    ConversationSessionDB.session_id
                    == session_id,
                    ConversationSessionDB.tenant_id
                    == tenant_id,
                )
                .first()
            )

            if session is not None:

                db.delete(
                    session,
                )

                db.commit()

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()

    # --------------------------------------------------------

    def _db_to_state(
        self,
        session: ConversationSessionDB,
    ) -> ConversationState:

        try:

            raw_items = json.loads(
                session.items_json or "[]",
            )

        except json.JSONDecodeError:

            raw_items = []

        items: list[IntentItem] = []

        for raw_item in raw_items:

            modifications: list[
                IntentModification
            ] = []

            for raw_modification in (
                raw_item.get(
                    "modifications",
                    [],
                )
            ):

                modifications.append(
                    IntentModification(
                        type=raw_modification[
                            "type"
                        ],
                        ingredient=(
                            raw_modification.get(
                                "ingredient",
                            )
                        ),
                        new_base=(
                            raw_modification.get(
                                "new_base",
                            )
                        ),
                    )
                )

            items.append(
                IntentItem(
                    product=raw_item[
                        "product"
                    ],
                    quantity=raw_item[
                        "quantity"
                    ],
                    modifications=modifications,
                )
            )

        return ConversationState(
            status=session.status,
            items=items,
            combo_requested=(
                session.combo_requested
            ),
            combo_product=(
                session.combo_product
            ),
            beverage_required=(
                session.beverage_required
            ),
            beverage_product_id=(
                session.beverage_product_id
            ),
            beverage_name=(
                session.beverage_name
            ),
            customer_id=(
                session.customer_id
            ),
            customer_name=(
                session.customer_name
            ),
            location_id=(
                session.location_id
            ),
        )

    # ========================================================
    # PROCESAMIENTO PRINCIPAL
    # ========================================================

    def process_message(
        self,
        session_id: str,
        message: str,
        customer_name: str,
        tenant: TenantContext,
        customer_id: int | None = None,
    ) -> dict:

        state = self.get_state(
            session_id,
            tenant.tenant_id,
        )

        # ----------------------------------------------------
        # Cliente
        # ----------------------------------------------------

        if customer_id is not None:

            if (
                state.customer_id is None
                or state.customer_id == customer_id
            ):

                state.customer_id = customer_id

        if state.customer_name is None:

            state.customer_name = (
                customer_name
            )

        # ====================================================
        # 1. ESTADOS CONVERSACIONALES PENDIENTES
        # ====================================================

        if (
            state.status
            == "waiting_combo_confirmation"
        ):

            return self._process_combo_confirmation(
                session_id=session_id,
                state=state,
                message=message,
                tenant=tenant,
            )

        if (
            state.status
            == "waiting_beverage"
        ):

            return self._process_beverage(
                session_id=session_id,
                state=state,
                message=message,
                tenant=tenant,
            )

        if (
            state.status
            == "awaiting_order_confirmation"
        ):

            return self._process_order_confirmation(
                session_id=session_id,
                state=state,
                message=message,
                tenant=tenant,
            )

        # ====================================================
        # 2. SI ESTAMOS ESPERANDO SEDE
        #
        # IMPORTANTE:
        # El mensaje de la sede NO debe volver a pasar por
        # parse_customer_message(), porque podría reemplazar
        # state.items con una interpretación vacía.
        #
        # Los productos y sus modificaciones ya pertenecen
        # al estado persistente de la conversación.
        # ====================================================

        if state.status == "waiting_location":

            locations = (
                location_service.find_locations(
                    message,
                    tenant.tenant_id,
                )
            )

            if len(locations) == 1:

                selected_location = locations[0]

                state.location_id = (
                    selected_location.id
                )

                # --------------------------------------------
                # Si todavía estamos ofreciendo combo,
                # mantenemos esa decisión pendiente.
                # --------------------------------------------

                if (
                    state.items
                    and state.combo_product
                    and not state.combo_requested
                ):

                    state.status = (
                        "waiting_combo_confirmation"
                    )

                    self._save_state(
                        session_id,
                        state,
                        tenant.tenant_id,
                    )

                    return {
                        "status": "needs_input",
                        "message": (
                            "Sede seleccionada: "
                            f"{selected_location.customer_name}. "
                            "¿Quieres llevar "
                            f"el {(
                                state.combo_product
                                or "producto"
                            ).lower()} en combo?"
                        ),
                        "customer_name": (
                            state.customer_name
                        ),
                        "customer_id": (
                            state.customer_id
                        ),
                        "location": {
                            "id": (
                                selected_location.id
                            ),
                            "name": (
                                selected_location.customer_name
                            ),
                            "toast_name": (
                                selected_location.toast_name
                            ),
                        },
                    }

                # --------------------------------------------
                # Si ya es combo y falta gaseosa.
                # --------------------------------------------

                if (
                    state.items
                    and state.combo_requested
                    and state.beverage_product_id
                    is None
                ):

                    state.status = (
                        "waiting_beverage"
                    )

                    state.beverage_required = True

                    self._save_state(
                        session_id,
                        state,
                        tenant.tenant_id,
                    )

                    return {
                        "status": "needs_input",
                        "message": (
                            "Sede seleccionada: "
                            f"{selected_location.customer_name}. "
                            "¿Qué gaseosa quieres con tu "
                            f"{(
                                state.combo_product
                                or "producto"
                            ).lower()}?"
                        ),
                        "customer_name": (
                            state.customer_name
                        ),
                        "customer_id": (
                            state.customer_id
                        ),
                        "location": {
                            "id": (
                                selected_location.id
                            ),
                            "name": (
                                selected_location.customer_name
                            ),
                            "toast_name": (
                                selected_location.toast_name
                            ),
                        },
                    }

                # --------------------------------------------
                # Pedido normal: conservar exactamente los
                # items persistidos, incluyendo modificaciones.
                # --------------------------------------------

                if state.items:

                    state.status = (
                        "awaiting_order_confirmation"
                    )

                    self._save_state(
                        session_id,
                        state,
                        tenant.tenant_id,
                    )

                    return {
                        "status": "needs_input",
                        "message": (
                            self._build_order_confirmation_message(
                                state,
                            )
                        ),
                        "customer_name": (
                            state.customer_name
                        ),
                        "customer_id": (
                            state.customer_id
                        ),
                        "location": {
                            "id": (
                                selected_location.id
                            ),
                            "name": (
                                selected_location.customer_name
                            ),
                            "toast_name": (
                                selected_location.toast_name
                            ),
                        },
                    }

                state.status = "waiting_product"

                self._save_state(
                    session_id,
                    state,
                    tenant.tenant_id,
                )

                return {
                    "status": "needs_input",
                    "message": (
                        "Sede seleccionada: "
                        f"{selected_location.customer_name}. "
                        "¿Qué producto deseas pedir?"
                    ),
                    "customer_name": (
                        state.customer_name
                    ),
                    "customer_id": (
                        state.customer_id
                    ),
                    "location": {
                        "id": (
                            selected_location.id
                        ),
                        "name": (
                            selected_location.customer_name
                        ),
                        "toast_name": (
                            selected_location.toast_name
                        ),
                    },
                }

            if len(locations) > 1:

                self._save_state(
                    session_id,
                    state,
                    tenant.tenant_id,
                )

                return {
                    "status": "needs_input",
                    "message": (
                        "Encontré varias sedes. "
                        "¿Cuál deseas utilizar?"
                    ),
                    "customer_name": (
                        state.customer_name
                    ),
                    "customer_id": (
                        state.customer_id
                    ),
                    "locations": [
                        {
                            "id": location.id,
                            "name": (
                                location.customer_name
                            ),
                            "toast_name": (
                                location.toast_name
                            ),
                        }
                        for location in locations
                    ],
                }

            return {
                "status": "needs_input",
                "message": (
                    "No encontré esa sede. "
                    "Puedes indicar Dirty Rabbit, "
                    "Wynwood Food Truck o Sunrise."
                ),
                "customer_name": (
                    state.customer_name
                ),
                "customer_id": (
                    state.customer_id
                ),
            }

        # ====================================================
        # 3. INTERPRETAR UN MENSAJE NUEVO
        # ====================================================

        intent = parse_customer_message(
            message,
        )

        # ----------------------------------------------------
        # Guardamos inmediatamente el intent interpretado.
        #
        # Esto es crítico: si el mensaje contiene una
        # modificación, por ejemplo "sin cebolla", la
        # modificación debe entrar al estado persistente
        # ANTES de resolver la sede.
        # ----------------------------------------------------

        if intent.status != "needs_input":

            state.items = list(
                intent.items,
            )

            if (
                intent.status
                == "needs_combo_confirmation"
            ):

                state.status = (
                    "waiting_combo_confirmation"
                )

                state.combo_requested = False

                state.combo_product = (
                    self._detect_combo_product(
                        intent.items,
                    )
                )

                state.beverage_required = False

                state.beverage_product_id = None

                state.beverage_name = None

            elif (
                intent.status
                == "needs_beverage"
            ):

                state.status = (
                    "waiting_beverage"
                )

                state.combo_requested = True

                state.combo_product = (
                    self._detect_combo_product(
                        intent.items,
                    )
                )

                state.beverage_required = True

            else:

                state.status = "ready"

                state.combo_requested = (
                    intent.combo_requested
                )

            # --------------------------------------------
            # Persistimos aquí antes de cualquier intento
            # de resolver la sede.
            # --------------------------------------------

            self._save_state(
                session_id,
                state,
                tenant.tenant_id,
            )

        # ====================================================
        # 4. RESOLVER SEDE EN UN MENSAJE NUEVO
        # ====================================================

        if state.location_id is None:

            locations = (
                location_service.find_locations(
                    message,
                    tenant.tenant_id,
                )
            )

            if len(locations) == 1:

                selected_location = locations[0]

                state.location_id = (
                    selected_location.id
                )

                if state.items:

                    if (
                        state.status
                        == "waiting_combo_confirmation"
                    ):

                        self._save_state(
                            session_id,
                            state,
                            tenant.tenant_id,
                        )

                        return {
                            "status": "needs_input",
                            "message": (
                                "Sede seleccionada: "
                                f"{selected_location.customer_name}. "
                                "¿Quieres llevar "
                                f"el {(
                                    state.combo_product
                                    or "producto"
                                ).lower()} en combo?"
                            ),
                            "customer_name": (
                                state.customer_name
                            ),
                            "customer_id": (
                                state.customer_id
                            ),
                            "location": {
                                "id": (
                                    selected_location.id
                                ),
                                "name": (
                                    selected_location.customer_name
                                ),
                                "toast_name": (
                                    selected_location.toast_name
                                ),
                            },
                        }

                    if (
                        state.status
                        == "waiting_beverage"
                    ):

                        self._save_state(
                            session_id,
                            state,
                            tenant.tenant_id,
                        )

                        return {
                            "status": "needs_input",
                            "message": (
                                "Sede seleccionada: "
                                f"{selected_location.customer_name}. "
                                "¿Qué gaseosa quieres con tu "
                                f"{(
                                    state.combo_product
                                    or "producto"
                                ).lower()}?"
                            ),
                            "customer_name": (
                                state.customer_name
                            ),
                            "customer_id": (
                                state.customer_id
                            ),
                            "location": {
                                "id": (
                                    selected_location.id
                                ),
                                "name": (
                                    selected_location.customer_name
                                ),
                                "toast_name": (
                                    selected_location.toast_name
                                ),
                            },
                        }

                    state.status = (
                        "awaiting_order_confirmation"
                    )

                    self._save_state(
                        session_id,
                        state,
                        tenant.tenant_id,
                    )

                    return {
                        "status": "needs_input",
                        "message": (
                            self._build_order_confirmation_message(
                                state,
                            )
                        ),
                        "customer_name": (
                            state.customer_name
                        ),
                        "customer_id": (
                            state.customer_id
                        ),
                        "location": {
                            "id": (
                                selected_location.id
                            ),
                            "name": (
                                selected_location.customer_name
                            ),
                            "toast_name": (
                                selected_location.toast_name
                            ),
                        },
                    }

                state.status = "waiting_product"

                self._save_state(
                    session_id,
                    state,
                    tenant.tenant_id,
                )

                return {
                    "status": "needs_input",
                    "message": (
                        "Sede seleccionada: "
                        f"{selected_location.customer_name}. "
                        "¿Qué producto deseas pedir?"
                    ),
                    "customer_name": (
                        state.customer_name
                    ),
                    "customer_id": (
                        state.customer_id
                    ),
                    "location": {
                        "id": (
                            selected_location.id
                        ),
                        "name": (
                            selected_location.customer_name
                        ),
                        "toast_name": (
                            selected_location.toast_name
                        ),
                    },
                }

            if len(locations) > 1:

                state.status = (
                    "waiting_location"
                )

                self._save_state(
                    session_id,
                    state,
                    tenant.tenant_id,
                )

                return {
                    "status": "needs_input",
                    "message": (
                        "Encontré varias sedes. "
                        "¿Cuál deseas utilizar?"
                    ),
                    "customer_name": (
                        state.customer_name
                    ),
                    "customer_id": (
                        state.customer_id
                    ),
                    "locations": [
                        {
                            "id": location.id,
                            "name": (
                                location.customer_name
                            ),
                            "toast_name": (
                                location.toast_name
                            ),
                        }
                        for location in locations
                    ],
                }

            if self._looks_like_location_request(
                message,
            ):

                locations = (
                    location_service
                    .get_all_active_locations(
                        tenant.tenant_id,
                    )
                )

                state.status = (
                    "waiting_location"
                )

                self._save_state(
                    session_id,
                    state,
                    tenant.tenant_id,
                )

                return {
                    "status": "needs_input",
                    "message": (
                        "¿En cuál sede deseas "
                        "realizar el pedido? "
                        "Puedes indicar Dirty Rabbit, "
                        "Wynwood Food Truck o Sunrise."
                    ),
                    "customer_name": (
                        state.customer_name
                    ),
                    "customer_id": (
                        state.customer_id
                    ),
                    "locations": [
                        {
                            "id": location.id,
                            "name": (
                                location.customer_name
                            ),
                            "toast_name": (
                                location.toast_name
                            ),
                        }
                        for location in locations
                    ],
                }

            if state.items:

                state.status = (
                    "waiting_location"
                )

                self._save_state(
                    session_id,
                    state,
                    tenant.tenant_id,
                )

                return {
                    "status": "needs_input",
                    "message": (
                        "¿En cuál sede deseas "
                        "realizar el pedido?"
                    ),
                    "customer_name": (
                        state.customer_name
                    ),
                    "customer_id": (
                        state.customer_id
                    ),
                }

            state.status = (
                "waiting_location"
            )

            self._save_state(
                session_id,
                state,
                tenant.tenant_id,
            )

            return {
                "status": "needs_input",
                "message": (
                    "¿En cuál sede deseas "
                    "realizar el pedido?"
                ),
                "customer_name": (
                    state.customer_name
                ),
                "customer_id": (
                    state.customer_id
                ),
            }

        # ====================================================
        # 5. YA TENEMOS SEDE
        # ====================================================

        if not state.items:

            state.status = (
                "waiting_product"
            )

            self._save_state(
                session_id,
                state,
                tenant.tenant_id,
            )

            return {
                "status": "needs_input",
                "message": (
                    intent.message
                    if intent.status == "needs_input"
                    else "¿Qué producto deseas pedir?"
                ),
                "customer_name": (
                    state.customer_name
                ),
                "customer_id": (
                    state.customer_id
                ),
            }

        # ====================================================
        # 6. PROCESAR INTENT
        # ====================================================

        if (
            intent.status
            == "needs_combo_confirmation"
        ):

            return self._process_intent(
                session_id=session_id,
                state=state,
                intent=intent,
                tenant=tenant,
            )

        if (
            intent.status
            == "needs_beverage"
        ):

            return self._process_intent(
                session_id=session_id,
                state=state,
                intent=intent,
                tenant=tenant,
            )

        return self._request_order_confirmation(
            session_id=session_id,
            state=state,
            tenant=tenant,
        )

    # ========================================================
    # INTENT
    # ========================================================

    def _process_intent(
        self,
        session_id: str,
        state: ConversationState,
        intent,
        tenant: TenantContext,
    ) -> dict:

        if (
            intent.status
            == "needs_combo_confirmation"
        ):

            state.status = (
                "waiting_combo_confirmation"
            )

            state.items = list(
                intent.items
            )

            state.combo_requested = False

            state.combo_product = (
                self._detect_combo_product(
                    intent.items,
                )
            )

            state.beverage_required = False

            state.beverage_product_id = None

            state.beverage_name = None

            self._save_state(
                session_id,
                state,
                tenant.tenant_id,
            )

            return {
                "status": "needs_input",
                "message": intent.message,
                "customer_name": (
                    state.customer_name
                ),
                "customer_id": (
                    state.customer_id
                ),
            }

        if (
            intent.status
            == "needs_beverage"
        ):

            state.status = (
                "waiting_beverage"
            )

            state.items = list(
                intent.items
            )

            state.combo_requested = True

            state.combo_product = (
                self._detect_combo_product(
                    intent.items,
                )
            )

            state.beverage_required = True

            self._save_state(
                session_id,
                state,
                tenant.tenant_id,
            )

            return {
                "status": "needs_input",
                "message": intent.message,
                "customer_name": (
                    state.customer_name
                ),
                "customer_id": (
                    state.customer_id
                ),
            }

        return self._request_order_confirmation(
            session_id=session_id,
            state=state,
            tenant=tenant,
        )

    # ========================================================
    # COMBO
    # ========================================================

    @staticmethod
    def _detect_combo_product(
        items: list[IntentItem],
    ) -> str | None:

        combo_products = {
            "PERRO DEL BARRIO",
            "PERRISIMO",
            "PERRO POLLO",
            "PERRO DESMECHADO",
            "PERRO HAWAIANO",
            "PERRO NEA",
            "CHORI - PERRO",
            "PERRO XL LPDB",
        }

        return next(
            (
                item.product
                for item in items
                if item.product
                in combo_products
            ),
            None,
        )

    # ========================================================
    # CONFIRMACIÓN DE COMBO
    # ========================================================

    def _process_combo_confirmation(
        self,
        session_id: str,
        state: ConversationState,
        message: str,
        tenant: TenantContext,
    ) -> dict:

        answer = _normalize(
            message,
        )

        if _is_yes(answer):

            state.status = (
                "waiting_beverage"
            )

            state.combo_requested = True

            state.beverage_required = True

            self._save_state(
                session_id,
                state,
                tenant.tenant_id,
            )

            return {
                "status": "needs_input",
                "message": (
                    "¿Qué gaseosa quieres con tu "
                    f"{(
                        state.combo_product
                        or "producto"
                    ).lower()}?"
                ),
                "customer_name": (
                    state.customer_name
                ),
                "customer_id": (
                    state.customer_id
                ),
            }

        if _is_no(answer):

            state.combo_requested = False

            state.combo_product = None

            state.beverage_required = False

            state.beverage_product_id = None

            state.beverage_name = None

            return self._request_order_confirmation(
                session_id=session_id,
                state=state,
                tenant=tenant,
            )

        return {
            "status": "needs_input",
            "message": (
                "¿Quieres llevarlo en combo? "
                "Responde SI o NO."
            ),
            "customer_name": (
                state.customer_name
            ),
            "customer_id": (
                state.customer_id
            ),
        }

    # ========================================================
    # BEBIDA
    # ========================================================

    def _process_beverage(
        self,
        session_id: str,
        state: ConversationState,
        message: str,
        tenant: TenantContext,
    ) -> dict:

        normalized_message = _normalize(
            message,
        )

        if not normalized_message:

            return {
                "status": "needs_input",
                "message": (
                    "¿Qué gaseosa quieres?"
                ),
                "customer_name": (
                    state.customer_name
                ),
                "customer_id": (
                    state.customer_id
                ),
            }

        from app.models.product_db import ProductDB

        db = SessionLocal()

        try:

            beverage = (
                db.query(
                    ProductDB,
                )
                .join(
                    ProductDB.category,
                )
                .filter(
                    ProductDB.tenant_id
                    == tenant.tenant_id,
                    ProductDB.name.isnot(None),
                )
                .all()
            )

            matches = []

            for product in beverage:

                category_name = (
                    product.category.name
                    if product.category is not None
                    else ""
                )

                if _normalize(
                    category_name,
                ) != "BEBIDAS":

                    continue

                product_name = _normalize(
                    product.name,
                )

                if (
                    product_name
                    == normalized_message
                ):

                    matches.append(
                        product,
                    )

            if len(matches) == 1:

                selected_beverage = matches[0]

                state.beverage_product_id = (
                    selected_beverage.id
                )

                state.beverage_name = (
                    selected_beverage.name
                )

                state.beverage_required = False

                self._save_state(
                    session_id,
                    state,
                    tenant.tenant_id,
                )

                return self._request_order_confirmation(
                    session_id=session_id,
                    state=state,
                    tenant=tenant,
                )

            partial_matches = []

            for product in beverage:

                category_name = (
                    product.category.name
                    if product.category is not None
                    else ""
                )

                if _normalize(
                    category_name,
                ) != "BEBIDAS":

                    continue

                product_name = _normalize(
                    product.name,
                )

                if (
                    normalized_message
                    in product_name
                    or product_name
                    in normalized_message
                ):

                    partial_matches.append(
                        product,
                    )

            if len(partial_matches) == 1:

                selected_beverage = (
                    partial_matches[0]
                )

                state.beverage_product_id = (
                    selected_beverage.id
                )

                state.beverage_name = (
                    selected_beverage.name
                )

                state.beverage_required = False

                self._save_state(
                    session_id,
                    state,
                    tenant.tenant_id,
                )

                return self._request_order_confirmation(
                    session_id=session_id,
                    state=state,
                    tenant=tenant,
                )

        finally:

            db.close()

        return {
            "status": "needs_input",
            "message": (
                "No encontré esa gaseosa. "
                "Indícame una gaseosa disponible, "
                "por ejemplo Coca Cola Normal."
            ),
            "customer_name": (
                state.customer_name
            ),
            "customer_id": (
                state.customer_id
            ),
        }

    # ========================================================
    # CONFIRMACIÓN FINAL DEL PEDIDO
    # ========================================================

    def _request_order_confirmation(
        self,
        session_id: str,
        state: ConversationState,
        tenant: TenantContext,
    ) -> dict:

        state.status = (
            "awaiting_order_confirmation"
        )

        self._save_state(
            session_id,
            state,
            tenant.tenant_id,
        )

        return {
            "status": "needs_input",
            "message": (
                self._build_order_confirmation_message(
                    state,
                )
            ),
            "customer_name": (
                state.customer_name
            ),
            "customer_id": (
                state.customer_id
            ),
        }

    # --------------------------------------------------------

    def _build_order_confirmation_message(
        self,
        state: ConversationState,
    ) -> str:

        item_lines = []

        for item in state.items:

            item_text = (
                f"{item.quantity} x "
                f"{item.product}"
            )

            modifications = []

            for modification in item.modifications:

                if modification.type == "REMOVE":

                    modifications.append(
                        "sin "
                        f"{modification.ingredient}"
                    )

                elif modification.type == "ADD":

                    modifications.append(
                        "con adicional de "
                        f"{modification.ingredient}"
                    )

                elif (
                    modification.type
                    == "BASE_CHANGE"
                ):

                    modifications.append(
                        "con base de "
                        f"{modification.new_base}"
                    )

            if modifications:

                item_text += (
                    " ("
                    + ", ".join(modifications)
                    + ")"
                )

            item_lines.append(
                item_text,
            )

        message = (
            "Este es tu pedido: "
            + ", ".join(item_lines)
        )

        if state.combo_requested:

            message += " en combo"

            if state.beverage_name:

                message += (
                    f" con {state.beverage_name}"
                )

        message += ". ¿Deseas confirmarlo?"

        return message

    # --------------------------------------------------------

    def _process_order_confirmation(
        self,
        session_id: str,
        state: ConversationState,
        message: str,
        tenant: TenantContext,
    ) -> dict:

        answer = _normalize(
            message,
        )

        if _is_yes(answer):

            return self._create_ready_order(
                session_id=session_id,
                customer_id=(
                    state.customer_id
                ),
                customer_name=(
                    state.customer_name
                    or "CLIENTE"
                ),
                items=state.items,
                combo_requested=(
                    state.combo_requested
                ),
                beverage_product_id=(
                    state.beverage_product_id
                ),
                beverage_product=(
                    state.beverage_name
                ),
                combo_product=(
                    state.combo_product
                ),
                location_id=(
                    state.location_id
                ),
                tenant=tenant,
            )

        if _is_no(answer):

            state.status = "ready"

            self._save_state(
                session_id,
                state,
                tenant.tenant_id,
            )

            return {
                "status": "needs_input",
                "message": (
                    "Perfecto. ¿Qué deseas "
                    "cambiar de tu pedido?"
                ),
                "customer_name": (
                    state.customer_name
                ),
                "customer_id": (
                    state.customer_id
                ),
            }

        return {
            "status": "needs_input",
            "message": (
                "¿Deseas confirmar tu pedido? "
                "Responde SI o NO."
            ),
            "customer_name": (
                state.customer_name
            ),
            "customer_id": (
                state.customer_id
            ),
        }

    # ========================================================
    # CREAR PEDIDO
    # ========================================================

    def _create_ready_order(
        self,
        session_id: str,
        customer_name: str,
        items: list[IntentItem],
        combo_requested: bool,
        tenant: TenantContext,
        customer_id: int | None = None,
        beverage_product_id: int | None = None,
        beverage_product: str | None = None,
        combo_product: str | None = None,
        location_id: int | None = None,
    ) -> dict:

        if location_id is None:

            return {
                "status": "needs_input",
                "message": (
                    "¿En cuál sede deseas "
                    "realizar el pedido?"
                ),
                "customer_name": customer_name,
                "customer_id": customer_id,
            }

        if not items:

            return {
                "status": "needs_input",
                "message": (
                    "¿Qué producto deseas pedir?"
                ),
                "customer_name": customer_name,
                "customer_id": customer_id,
            }

        order_items: list[
            OrderItemCreate
        ] = []

        for item in items:

            item_combo_requested = (
                combo_requested
                and combo_product is not None
                and item.product
                == combo_product
            )

            modifications = [
                _to_order_modification(
                    modification,
                )
                for modification
                in item.modifications
            ]

            order_items.append(
                OrderItemCreate(
                    product=item.product,
                    quantity=item.quantity,
                    modifications=modifications,
                    combo_requested=(
                        item_combo_requested
                    ),
                    beverage_product_id=(
                        beverage_product_id
                        if item_combo_requested
                        else None
                    ),
                    beverage_product=(
                        beverage_product
                        if item_combo_requested
                        else None
                    ),
                )
            )

        try:

            order = OrderCreate(
                customer_name=customer_name,
                customer_id=customer_id,
                location_id=location_id,
                items=order_items,
            )

            saved_order = create_order(
                order,
                tenant,
            )

        except ValueError as exc:

            return {
                "status": "error",
                "message": str(exc),
                "customer_name": customer_name,
                "customer_id": customer_id,
            }

        self._clear_state(
            session_id,
            tenant.tenant_id,
        )

        response = {
            "status": "ready",
            "message": None,
            "customer_name": customer_name,
            "customer_id": customer_id,
            "order": saved_order,
            "items": [
                {
                    "product": item.product,
                    "quantity": item.quantity,
                    "modifications": [
                        {
                            "type": modification.type,
                            "ingredient": (
                                modification.ingredient
                            ),
                            "new_base": (
                                modification.new_base
                            ),
                        }
                        for modification
                        in item.modifications
                    ],
                }
                for item in items
            ],
            "combo_requested": (
                combo_requested
            ),
            "location_id": location_id,
        }

        if combo_requested:

            response["beverage"] = {
                "product_id": (
                    beverage_product_id
                ),
                "product": (
                    beverage_product
                ),
            }

        return response

    # ========================================================
    # UBICACIÓN
    # ========================================================

    def _looks_like_location_request(
        self,
        message: str,
    ) -> bool:

        normalized = _normalize(
            message,
        )

        location_keywords = {
            "SEDE",
            "LOCAL",
            "UBICACION",
            "UBICACIÓN",
            "DONDE",
            "DÓNDE",
            "LUGAR",
            "TIENDA",
        }

        tokens = set(
            normalized.split()
        )

        return bool(
            tokens
            & location_keywords
        )


# ============================================================
# SINGLETON
# ============================================================


conversation_service = ConversationService()
