# runs the delivery simulation tick by tick:
# assign orders -> calculate routes -> move bots -> handle pickups/deliveries

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Bot, Order, Node, Restaurant
from app.models.bot import BotStatus
from app.models.order import OrderStatus
from app.services.pathfinding import PathfindingService

# restaurants can only handle 3 orders every 30 ticks
# this prevents spamming one restaurant with a ton of orders at once
RESTAURANT_ORDER_LIMIT = 3
RESTAURANT_COOLDOWN_TICKS = 30


class SimulationService:

    # track tick count and restaurant order history across ticks
    # class-level so it persists between service instantiations
    _tick_counter: int = 0
    _restaurant_order_log: Dict[int, List[int]] = {}

    def __init__(self, db: Session):
        self.db = db
        self.pathfinder = PathfindingService(db)
        self._bot_routes: Dict[int, List[int]] = {}
        # target is (node_id, 'PICKUP'|'DELIVER', order_id)
        self._bot_targets: Dict[int, tuple] = {}

    def tick(self) -> Dict:
        SimulationService._tick_counter += 1

        results = {
            "orders_assigned": 0,
            "orders_picked_up": 0,
            "orders_delivered": 0,
            "bots_moved": 0,
        }

        results["orders_assigned"] = self._assign_pending_orders()
        self._calculate_bot_routes()

        move_results = self._move_bots()
        results["bots_moved"] = move_results["moved"]
        results["orders_picked_up"] = move_results["picked_up"]
        results["orders_delivered"] = move_results["delivered"]

        return results

    def _get_restaurant_orders_in_window(self, restaurant_id: int) -> int:
        # how many orders this restaurant got assigned in the last N ticks
        current_tick = SimulationService._tick_counter
        log = SimulationService._restaurant_order_log.get(restaurant_id, [])

        # only count ticks within the cooldown window
        recent = [t for t in log if current_tick - t < RESTAURANT_COOLDOWN_TICKS]
        SimulationService._restaurant_order_log[restaurant_id] = recent
        return len(recent)

    def _log_restaurant_order(self, restaurant_id: int):
        current_tick = SimulationService._tick_counter
        if restaurant_id not in SimulationService._restaurant_order_log:
            SimulationService._restaurant_order_log[restaurant_id] = []
        SimulationService._restaurant_order_log[restaurant_id].append(current_tick)

    def _assign_pending_orders(self) -> int:
        # assign each pending order to the closest bot that actually has room
        assigned = 0

        pending_orders = self.db.query(Order).filter(
            Order.status == OrderStatus.PENDING
        ).all()

        # track how many we assign to each bot THIS tick so we don't
        # blow past capacity by assigning multiple in the same loop
        extra_assignments: Dict[int, int] = {}

        for order in pending_orders:
            # check restaurant cooldown first
            if self._get_restaurant_orders_in_window(order.restaurant_id) >= RESTAURANT_ORDER_LIMIT:
                # this restaurant is at capacity, skip for now
                continue

            available_bots = self.db.query(Bot).filter(
                Bot.status.in_([BotStatus.IDLE, BotStatus.MOVING])
            ).all()

            best_bot = None
            best_distance = float('inf')

            for bot in available_bots:
                # count orders already in the db
                db_orders = self.db.query(Order).filter(
                    Order.bot_id == bot.id,
                    Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])
                ).count()

                # plus any we just assigned this tick that haven't been committed yet
                pending_extra = extra_assignments.get(bot.id, 0)
                total_orders = db_orders + pending_extra

                if total_orders >= bot.max_capacity:
                    continue

                if bot.current_node_id:
                    distance = self.pathfinder.get_path_length(
                        bot.current_node_id,
                        order.pickup_node_id
                    )
                    if distance is not None and distance < best_distance:
                        best_distance = distance
                        best_bot = bot

            if best_bot:
                order.bot_id = best_bot.id
                order.status = OrderStatus.ASSIGNED
                order.assigned_at = datetime.utcnow()

                if best_bot.status == BotStatus.IDLE:
                    best_bot.status = BotStatus.MOVING

                # track this assignment so the next iteration knows about it
                extra_assignments[best_bot.id] = extra_assignments.get(best_bot.id, 0) + 1
                self._log_restaurant_order(order.restaurant_id)
                assigned += 1

        self.db.commit()
        return assigned

    def _calculate_bot_routes(self):
        # pick up assigned orders first, then deliver picked-up ones
        bots = self.db.query(Bot).filter(
            Bot.status.in_([BotStatus.MOVING, BotStatus.IDLE])
        ).all()

        for bot in bots:
            if bot.id in self._bot_routes and self._bot_routes[bot.id]:
                continue

            orders = self.db.query(Order).filter(
                Order.bot_id == bot.id,
                Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])
            ).all()

            if not orders:
                if bot.status != BotStatus.IDLE:
                    bot.status = BotStatus.IDLE
                continue

            assigned_orders = [o for o in orders if o.status == OrderStatus.ASSIGNED]
            picked_up_orders = [o for o in orders if o.status == OrderStatus.PICKED_UP]

            target_node = None
            action = None
            target_order = None

            if assigned_orders:
                # head to closest restaurant
                closest_order = min(
                    assigned_orders,
                    key=lambda o: self.pathfinder.get_path_length(
                        bot.current_node_id, o.pickup_node_id
                    ) or float('inf')
                )
                target_node = closest_order.pickup_node_id
                action = "PICKUP"
                target_order = closest_order
            elif picked_up_orders:
                # head to closest delivery point
                closest_order = min(
                    picked_up_orders,
                    key=lambda o: self.pathfinder.get_path_length(
                        bot.current_node_id, o.delivery_node_id
                    ) or float('inf')
                )
                target_node = closest_order.delivery_node_id
                action = "DELIVER"
                target_order = closest_order

            if target_node and bot.current_node_id:
                path = self.pathfinder.find_path(bot.current_node_id, target_node)
                if path:
                    self._bot_routes[bot.id] = path[1:] if len(path) > 1 else []
                    self._bot_targets[bot.id] = (target_node, action, target_order.id if target_order else None)

        self.db.commit()

    def _move_bots(self) -> Dict:
        # advance each moving bot one step along its route
        results = {"moved": 0, "picked_up": 0, "delivered": 0}

        bots = self.db.query(Bot).filter(
            Bot.status == BotStatus.MOVING
        ).all()

        for bot in bots:
            route = self._bot_routes.get(bot.id, [])

            if not route:
                self._handle_arrival(bot, results)
                continue

            next_node_id = route.pop(0)
            bot.current_node_id = next_node_id
            results["moved"] += 1

            self._bot_routes[bot.id] = route

            if not route:
                self._handle_arrival(bot, results)

        self.db.commit()
        return results

    def _handle_arrival(self, bot: Bot, results: Dict):
        target_info = self._bot_targets.get(bot.id)
        if not target_info:
            return

        target_node, action, order_id = target_info

        if bot.current_node_id != target_node:
            return

        if action == "PICKUP":
            # grab all assigned orders at this restaurant node
            orders = self.db.query(Order).filter(
                Order.bot_id == bot.id,
                Order.status == OrderStatus.ASSIGNED,
                Order.pickup_node_id == target_node
            ).all()

            for order in orders:
                order.status = OrderStatus.PICKED_UP
                order.picked_up_at = datetime.utcnow()
                results["picked_up"] += 1

            bot.status = BotStatus.PICKING_UP

        elif action == "DELIVER":
            # drop off all picked-up orders for this location
            orders = self.db.query(Order).filter(
                Order.bot_id == bot.id,
                Order.status == OrderStatus.PICKED_UP,
                Order.delivery_node_id == target_node
            ).all()

            for order in orders:
                order.status = OrderStatus.DELIVERED
                order.delivered_at = datetime.utcnow()
                results["delivered"] += 1

            bot.status = BotStatus.DELIVERING

        # clear target so it recalculates next tick
        del self._bot_targets[bot.id]
        self._bot_routes[bot.id] = []

        remaining_orders = self.db.query(Order).filter(
            Order.bot_id == bot.id,
            Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])
        ).count()

        if remaining_orders == 0:
            bot.status = BotStatus.IDLE
        else:
            bot.status = BotStatus.MOVING

    def get_bot_route(self, bot_id: int) -> List[int]:
        return self._bot_routes.get(bot_id, [])

    def get_bot_target(self, bot_id: int) -> Optional[tuple]:
        return self._bot_targets.get(bot_id)
