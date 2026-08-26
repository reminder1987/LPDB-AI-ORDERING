import json
import unicodedata

from dataclasses import dataclass, field

from app.core.database import SessionLocal

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

    def _save_state(
        self,
        session_id: str,
        state: ConversationState,
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
                )
                .first()
            )

            if session is None:

                session = ConversationSessionDB(
                    session_id=session_id,
                )

                db.add(session)

            session.status = state.status

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
    ) -> dict:

        state = self.get_state(
            session_id,
        )

        # ----------------------------------------------------
        # Cliente
        # ----------------------------------------------------

        if state.customer_name is None:

            state.customer_name = (
                customer_name
            )

        # ====================================================
        # 1. ESTADOS CONVERSACIONALES PENDIENTES
        #
        # Estos estados tienen prioridad porque una respuesta
        # como "Sí" o "Coca Cola Normal" no debe interpretarse
        # como un pedido nuevo.
        # ====================================================

        if (
            state.status
            == "waiting_combo_confirmation"
        ):

            return self._process_combo_confirmation(
                session_id=session_id,
                state=state,
                message=message,
            )

        if (
            state.status
            == "waiting_beverage"
        ):

            return self._process_beverage(
                session_id=session_id,
                state=state,
                message=message,
            )

        # ====================================================
        # 2. INTERPRETAR EL MENSAJE
        #
        # IMPORTANTE:
        #
        # Primero intentamos descubrir productos.
        #
        # Esto permite conservar el pedido mientras esperamos
        # una sede.
        # ====================================================

        intent = parse_customer_message(
            message,
        )

        # ----------------------------------------------------
        # Si encontramos productos, actualizamos el estado.
        #
        # La sede puede venir en el mismo mensaje o todavía
        # faltar.
        # ----------------------------------------------------

        if intent.status != "needs_input":

            state.items = list(
                intent.items,
            )

            # ------------------------------------------------
            # Combo pendiente de confirmación
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Combo que ya requiere bebida
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Pedido normal
            # ------------------------------------------------

            else:

                state.status = "ready"

                state.combo_requested = (
                    intent.combo_requested
                )

        # ====================================================
        # 3. RESOLVER SEDE
        # ====================================================

        if state.location_id is None:

            locations = (
                location_service.find_locations(
                    message,
                )
            )

            # ------------------------------------------------
            # Una sola sede encontrada
            # ------------------------------------------------

            if len(locations) == 1:

                selected_location = locations[0]

                state.location_id = (
                    selected_location.id
                )

                # --------------------------------------------
                # Si hay productos pendientes, podemos
                # continuar inmediatamente.
                # --------------------------------------------

                if state.items:

                    self._save_state(
                        session_id,
                        state,
                    )

                    if (
                        state.status
                        == "waiting_combo_confirmation"
                    ):

                        return {
                            "status": "needs_input",
                            "message": (
                                "Sede seleccionada: "
                                f"{selected_location.customer_name}. "
                                + (
                                    "¿Quieres llevar "
                                    f"el {(
                                        state.combo_product
                                        or 'producto'
                                    ).lower()} en combo?"
                                )
                            ),
                            "customer_name": (
                                state.customer_name
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

                        return {
                            "status": "needs_input",
                            "message": (
                                "Sede seleccionada: "
                                f"{selected_location.customer_name}. "
                                + (
                                    "¿Qué gaseosa quieres con tu "
                                    f"{(
                                        state.combo_product
                                        or 'producto'
                                    ).lower()}?"
                                )
                            ),
                            "customer_name": (
                                state.customer_name
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

                    return self._create_ready_order(
                        session_id=session_id,
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
                    )

                # --------------------------------------------
                # Encontramos sede pero no producto.
                # --------------------------------------------

                state.status = "waiting_product"

                self._save_state(
                    session_id,
                    state,
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

            # ------------------------------------------------
            # Varias sedes
            # ------------------------------------------------

            if len(locations) > 1:

                state.status = (
                    "waiting_location"
                )

                self._save_state(
                    session_id,
                    state,
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

            # ------------------------------------------------
            # El mensaje parece pedir una sede pero no
            # corresponde a una sede específica.
            # ------------------------------------------------

            if self._looks_like_location_request(
                message,
            ):

                locations = (
                    location_service
                    .get_all_active_locations()
                )

                state.status = (
                    "waiting_location"
                )

                self._save_state(
                    session_id,
                    state,
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

            # ------------------------------------------------
            # No encontramos sede.
            #
            # Si ya tenemos productos, los conservamos.
            # ------------------------------------------------

            if state.items:

                state.status = (
                    "waiting_location"
                )

                self._save_state(
                    session_id,
                    state,
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
                }

            # ------------------------------------------------
            # No tenemos ni sede ni producto.
            # ------------------------------------------------

            state.status = (
                "waiting_location"
            )

            self._save_state(
                session_id,
                state,
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
            }

        # ====================================================
        # 4. YA TENEMOS SEDE
        # ====================================================

        # Si el intent no encontró productos, preguntamos
        # por el producto.
        if not state.items:

            state.status = (
                "waiting_product"
            )

            self._save_state(
                session_id,
                state,
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
            }

        # ====================================================
        # 5. PROCESAR INTENT
        # ====================================================

        if (
            intent.status
            == "needs_combo_confirmation"
        ):

            return self._process_intent(
                session_id=session_id,
                state=state,
                intent=intent,
            )

        if (
            intent.status
            == "needs_beverage"
        ):

            return self._process_intent(
                session_id=session_id,
                state=state,
                intent=intent,
            )

        return self._create_ready_order(
            session_id=session_id,
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
        )

    # ========================================================
    # INTENT
    # ========================================================

    def _process_intent(
        self,
        session_id: str,
        state: ConversationState,
        intent,
    ) -> dict:

        # ----------------------------------------------------
        # COMBO: confirmar
        # ----------------------------------------------------

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
            )

            return {
                "status": "needs_input",
                "message": intent.message,
                "customer_name": (
                    state.customer_name
                ),
            }

        # ----------------------------------------------------
        # COMBO: requiere bebida
        # ----------------------------------------------------

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
            )

            return {
                "status": "needs_input",
                "message": intent.message,
                "customer_name": (
                    state.customer_name
                ),
            }

        # ----------------------------------------------------
        # Pedido listo
        # ----------------------------------------------------

        return self._create_ready_order(
            session_id=session_id,
            customer_name=(
                state.customer_name
                or "CLIENTE"
            ),
            items=intent.items,
            combo_requested=(
                intent.combo_requested
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
    ) -> dict:

        answer = _normalize(
            message,
        )

        # ----------------------------------------------------
        # SI
        # ----------------------------------------------------

        if _is_yes(answer):

            state.status = (
                "waiting_beverage"
            )

            state.combo_requested = True

            state.beverage_required = True

            self._save_state(
                session_id,
                state,
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
            }

        # ----------------------------------------------------
        # NO
        # ----------------------------------------------------

        if _is_no(answer):

            return self._create_ready_order(
                session_id=session_id,
                customer_name=(
                    state.customer_name
                    or "CLIENTE"
                ),
                items=state.items,
                combo_requested=False,
                combo_product=None,
                location_id=state.location_id,
            )

        # ----------------------------------------------------
        # RESPUESTA INVÁLIDA
        # ----------------------------------------------------

        return {
            "status": "needs_input",
            "message": (
                "¿Quieres llevarlo en combo? "
                "Responde SI o NO."
            ),
            "customer_name": (
                state.customer_name
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
                    ProductDB.name
                    .isnot(None),
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
                )

                return self._create_ready_order(
                    session_id=session_id,
                    customer_name=(
                        state.customer_name
                        or "CLIENTE"
                    ),
                    items=state.items,
                    combo_requested=True,
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
                )

            # ------------------------------------------------
            # Búsqueda parcial
            # ------------------------------------------------

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
                )

                return self._create_ready_order(
                    session_id=session_id,
                    customer_name=(
                        state.customer_name
                        or "CLIENTE"
                    ),
                    items=state.items,
                    combo_requested=True,
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
                )

        finally:

            db.close()

        # ----------------------------------------------------
        # No encontrada
        # ----------------------------------------------------

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
        beverage_product_id: int | None = None,
        beverage_product: str | None = None,
        combo_product: str | None = None,
        location_id: int | None = None,
    ) -> dict:

        # ----------------------------------------------------
        # Sede
        # ----------------------------------------------------

        if location_id is None:

            return {
                "status": "needs_input",
                "message": (
                    "¿En cuál sede deseas "
                    "realizar el pedido?"
                ),
                "customer_name": customer_name,
            }

        # ----------------------------------------------------
        # Productos
        # ----------------------------------------------------

        if not items:

            return {
                "status": "needs_input",
                "message": (
                    "¿Qué producto deseas pedir?"
                ),
                "customer_name": customer_name,
            }

        # ----------------------------------------------------
        # Construir todos los items
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Crear OrderCreate
        # ----------------------------------------------------

        try:

            order = OrderCreate(
                customer_name=customer_name,
                location_id=location_id,
                items=order_items,
            )

            saved_order = create_order(
                order,
            )

        except ValueError as exc:

            return {
                "status": "error",
                "message": str(exc),
                "customer_name": customer_name,
            }

        # ----------------------------------------------------
        # Pedido terminado.
        #
        # Eliminamos la sesión persistida.
        # ----------------------------------------------------

        self._clear_state(
            session_id,
        )

        response = {
            "status": "ready",
            "message": None,
            "customer_name": customer_name,
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