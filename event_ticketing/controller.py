from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Enumerations
class TicketStatus(Enum):
    AVAILABLE = "AVAILABLE"
    SOLD = "SOLD"
    REFUNDED = "REFUNDED"

class OrderStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"

class PaymentStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RefundStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

# Classes
class User:
    user_counter = 0  # Static counter for User IDs

    def __init__(self, name: str, email: str, password: str, roles: List[str]):
        User.user_counter += 1
        self.__id = User.user_counter  # Auto-generate ID
        self.__name = name
        self.__email = email
        self.__password = password
        self.__roles = roles

    # Getter for id
    @property
    def id(self):
        return self.__id

    # Getter for name
    @property
    def name(self):
        return self.__name

    # Getter for email
    @property
    def email(self):
        return self.__email

    # Getter for roles
    @property
    def roles(self):
        return self.__roles

    def has_role(self, role: str) -> bool:
        return role in self.__roles

    def add_role(self, role: str):
        if role not in self.__roles:
            self.__roles.append(role)
            logging.info(f"Role '{role}' added to user '{self.name}'.")

    def remove_role(self, role: str):
        if role in self.__roles:
            self.__roles.remove(role)
            logging.info(f"Role '{role}' removed from user '{self.name}'.")

    def verify_password(self, password: str) -> bool:
        return self.__password == password

class Event:
    event_counter = 0  # Static counter for Event IDs

    def __init__(self, name: str, date: datetime, organizer: User, hall: 'Hall'):
        Event.event_counter += 1
        self.__id = Event.event_counter  # Auto-generate ID
        self.__name = name
        self.__date = date
        self.__organizer = organizer
        self.__hall = hall
        self.__zones: Dict[str, 'Zone'] = {}

    # Getter for id
    @property
    def id(self):
        return self.__id

    # Getter for name
    @property
    def name(self):
        return self.__name

    # Getter for date
    @property
    def date(self):
        return self.__date

    # Getter for zones
    @property
    def zones(self):
        return self.__zones

    def add_zone(self, zone: 'Zone', user: User):
        if not user.has_role("EventOrganizer"):
            logging.error(f"User '{user.name}' does not have permission to add zones.")
            return False
        self.__zones[zone.type] = zone
        logging.info(f"Zone '{zone.type}' added to event '{self.name}'.")
        return True

    def add_zone_with_percentage(self, zone_type: str, percentage: float, price: float, user: User):
        """
        Add a zone with a percentage of the hall's capacity.
        :param zone_type: Type of the zone (e.g., "VIP", "Regular")
        :param percentage: Percentage of the hall's capacity (e.g., 0.2 for 20%)
        :param price: Price of tickets in this zone
        :param user: User adding the zone (must be an EventOrganizer)
        """
        if not user.has_role("EventOrganizer"):
            logging.error(f"User '{user.name}' does not have permission to add zones.")
            return False
        capacity = int(self.__hall.capacity * percentage)
        zone = Zone(type=zone_type, capacity=capacity, price=price, event=self)
        self.add_zone(zone, user)
        logging.info(f"Zone '{zone_type}' added with {capacity} seats ({percentage * 100}% of hall capacity).")
        return True

    def display_event_info(self):
        """Display information about the event."""
        print(f"Event ID: {self.id}")
        print(f"Event Name: {self.name}")
        print(f"Event Date: {self.date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Organizer: {self.__organizer.name}")
        print("Zones:")
        for zone_type, zone in self.__zones.items():
            print(f"  - {zone_type}: {zone.get_available_tickets_count()} available tickets out of {zone.capacity}")

class Hall:
    hall_counter = 0  # Static counter for Hall IDs

    def __init__(self, size: str, capacity: int):
        Hall.hall_counter += 1
        self.__id = Hall.hall_counter  # Auto-generate ID
        self.__size = size
        self.__capacity = capacity

    # Getter for id
    @property
    def id(self):
        return self.__id

    # Getter for size
    @property
    def size(self):
        return self.__size

    # Getter for capacity
    @property
    def capacity(self):
        return self.__capacity

class Zone:
    zone_counter = 0  # Static counter for Zone IDs

    def __init__(self, type: str, capacity: int, price: float, event: 'Event'):
        Zone.zone_counter += 1
        self.__id = Zone.zone_counter  # Auto-generate ID
        self.__type = type
        self.__capacity = capacity
        self.__price = price
        self.__event = event
        self.__tickets: List['Ticket'] = [Ticket(zone=self) for _ in range(capacity)]

    # Getter for type
    @property
    def type(self):
        return self.__type

    # Getter for price
    @property
    def price(self):
        return self.__price

    # Getter for capacity
    @property
    def capacity(self):
        return self.__capacity

    # Getter for tickets
    @property
    def tickets(self):
        return self.__tickets

    # Getter for event
    @property
    def event(self):
        return self.__event

    def get_available_tickets(self, quantity: int) -> List['Ticket']:
        available_tickets = [ticket for ticket in self.__tickets if ticket.status == TicketStatus.AVAILABLE]
        if len(available_tickets) == 0:
            logging.warning(f"No tickets available in zone '{self.type}'.")
        return available_tickets[:quantity]

    def get_available_tickets_count(self) -> int:
        """Get the number of available tickets in the zone."""
        available_tickets = [ticket for ticket in self.__tickets if ticket.status == TicketStatus.AVAILABLE]
        return len(available_tickets)

class Ticket:
    ticket_counter = 0  # Static counter for Ticket IDs

    def __init__(self, zone: 'Zone'):
        Ticket.ticket_counter += 1
        self.__id = Ticket.ticket_counter  # Auto-generate ID
        self.__zone = zone
        self.__buyer: Optional[User] = None
        self.__status = TicketStatus.AVAILABLE

    # Getter for id
    @property
    def id(self):
        return self.__id

    # Getter for zone
    @property
    def zone(self):
        return self.__zone

    # Getter for status
    @property
    def status(self):
        return self.__status

    # Setter for status
    @status.setter
    def status(self, value: TicketStatus):
        self.__status = value

    def purchase(self, buyer: User) -> bool:
        if self.__status == TicketStatus.AVAILABLE:
            self.__buyer = buyer
            self.__status = TicketStatus.SOLD
            logging.info(f"Ticket {self.__id} purchased by {buyer.name}.")
            return True
        return False

    def refund(self) -> bool:
        if self.__status == TicketStatus.SOLD and self.__buyer:
            self.__status = TicketStatus.REFUNDED
            logging.info(f"Ticket {self.__id} refunded.")
            return True
        return False

class Order:
    order_counter = 0  # Static counter for Order IDs

    def __init__(self, buyer: User):
        Order.order_counter += 1
        self.__id = Order.order_counter  # Auto-generate ID
        self.__buyer = buyer
        self.__tickets: List[Ticket] = []
        self.__total_price: float = 0.0
        self.__status = OrderStatus.PENDING

    # Getter for id
    @property
    def id(self):
        return self.__id

    # Getter for status
    @property
    def status(self):
        return self.__status

    # Getter for buyer
    @property
    def buyer(self):
        return self.__buyer

    def add_ticket(self, ticket: Ticket):
        self.__tickets.append(ticket)
        self.__total_price += ticket.zone.price

    def complete_order(self) -> bool:
        if self.__status == OrderStatus.PENDING:
            if not self.__tickets:
                logging.error(f"Order {self.__id} has no tickets to complete.")
                return False
            self.__status = OrderStatus.COMPLETED
            payment = Payment(order=self, amount=self.__total_price)
            if payment.process_payment(success=True):
                logging.info(f"Order {self.__id} completed successfully.")
                return True
            else:
                self.__status = OrderStatus.PENDING
                logging.error(f"Payment for order {self.__id} failed.")
                return False
        return False

    def display_order_tickets(self):
        """Display the tickets in the order."""
        print(f"Order ID: {self.id}")
        print(f"Buyer: {self.__buyer.name}")
        print("Tickets:")
        for ticket in self.__tickets:
            print(f"  - Ticket ID: {ticket.id}, Zone: {ticket.zone.type}, Status: {ticket.status.name}")

class Payment:
    payment_counter = 0  # Static counter for Payment IDs

    def __init__(self, order: Order, amount: float):
        Payment.payment_counter += 1
        self.__id = Payment.payment_counter  # Auto-generate ID
        self.__order = order
        self.__amount = amount
        self.__status = PaymentStatus.PENDING

    # Getter for status
    @property
    def status(self):
        return self.__status

    def process_payment(self, success: bool) -> bool:
        if success:
            self.__status = PaymentStatus.COMPLETED
            logging.info(f"Payment {self.__id} completed successfully.")
            return True
        else:
            self.__status = PaymentStatus.FAILED
            logging.error(f"Payment {self.__id} failed.")
            return False

class RefundRequest:
    refund_counter = 0  # Static counter for Refund IDs

    def __init__(self, ticket: Ticket, buyer: User):
        RefundRequest.refund_counter += 1
        self.__id = RefundRequest.refund_counter  # Auto-generate ID
        self.__ticket = ticket
        self.__buyer = buyer
        self.__status = RefundStatus.PENDING
        self.__refund_amount = ticket.zone.price

    # Getter for status
    @property
    def status(self):
        return self.__status

    def approve_refund(self) -> bool:
        if self.__status == RefundStatus.PENDING:
            self.__status = RefundStatus.APPROVED
            self.__ticket.refund()
            logging.info(f"Refund request {self.__id} approved.")
            return True
        return False

    def reject_refund(self) -> bool:
        if self.__status == RefundStatus.PENDING:
            self.__status = RefundStatus.REJECTED
            logging.info(f"Refund request {self.__id} rejected.")
            return True
        return False

class UserTickets:
    def __init__(self, user: User):
        self.__user = user
        self.__tickets: List[Ticket] = []

    # Getter for user
    @property
    def user(self):
        return self.__user

    # Getter for tickets
    @property
    def tickets(self):
        return self.__tickets

    def add_ticket(self, ticket: Ticket):
        self.__tickets.append(ticket)
        logging.info(f"Ticket {ticket.id} added to user '{self.__user.name}'.")

    def display_tickets(self):
        """Display the tickets owned by the user."""
        print(f"User: {self.__user.name}")
        print("Tickets:")
        for ticket in self.__tickets:
            print(f"  - Ticket ID: {ticket.id}, Event: {ticket.zone.event.name}, Zone: {ticket.zone.type}, Status: {ticket.status.name}")

# Controller Class
class Controller:
    def __init__(self):
        self.__users: List[User] = []
        self.__events: List[Event] = []
        self.__orders: List[Order] = []
        self.__payments: List[Payment] = []
        self.__refund_requests: List[RefundRequest] = []
        self.__user_tickets: Dict[int, UserTickets] = {}
        self.__halls: List[Hall] = []

    # User Management
    def create_user(self, name: str, email: str, password: str, roles: List[str]) -> User:
        user = User(name=name, email=email, password=password, roles=roles)
        self.__users.append(user)
        self.__user_tickets[user.id] = UserTickets(user=user)
        logging.info(f"User '{name}' created with roles: {roles}.")
        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        for user in self.__users:
            if user.id == user_id:
                return user
        logging.warning(f"User with ID {user_id} not found.")
        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self.__users:
            if user.email == email:
                return user
        logging.warning(f"User with email {email} not found.")
        return None

    def add_ticket_to_user(self, user: User, ticket: Ticket):
        if user.id in self.__user_tickets:
            self.__user_tickets[user.id].add_ticket(ticket)

    def display_user_tickets(self, user_id: int):
        if user_id in self.__user_tickets:
            self.__user_tickets[user_id].display_tickets()
        else:
            logging.error(f"User with ID {user_id} not found.")

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if user and user.verify_password(password):
            return user
        logging.warning(f"Authentication failed for email: {email}")
        return None

    def get_user_tickets(self, user_id: int) -> List[Ticket]:
        if user_id in self.__user_tickets:
            return self.__user_tickets[user_id].tickets
        logging.warning(f"User with ID {user_id} not found.")
        return []

    # Event Management
    def create_event(self, name: str, date: datetime, organizer: User, hall: Hall, zones: List[Dict[str, float]]) -> Event:
        """
        Create an event and automatically add zones.
        :param name: Name of the event
        :param date: Date of the event
        :param organizer: Organizer of the event
        :param hall: Hall where the event will be held
        :param zones: List of zones to be added with their percentage and price
        :return: Created Event object
        """
        event = Event(name=name, date=date, organizer=organizer, hall=hall)
        self.__events.append(event)
        logging.info(f"Event '{name}' created by '{organizer.name}'.")

        for zone in zones:
            self.add_zone_to_event(event_id=event.id, zone_type=zone['type'], percentage=zone['percentage'], price=zone['price'], user=organizer)

        return event

    def add_zone_to_event(self, event_id: int, zone_type: str, percentage: float, price: float, user: User) -> bool:
        event = self.get_event_by_id(event_id)
        if event:
            return event.add_zone_with_percentage(zone_type=zone_type, percentage=percentage, price=price, user=user)
        return False

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        for event in self.__events:
            if event.id == event_id:
                return event
        logging.warning(f"Event with ID {event_id} not found.")
        return None

    def display_event_info(self, event_id: int):
        event = self.get_event_by_id(event_id)
        if event:
            event.display_event_info()
        else:
            logging.error(f"Event with ID {event_id} not found.")

    def get_events(self) -> List[Event]:
        return self.__events

    # Order Management
    def create_order(self, buyer: User) -> Order:
        order = Order(buyer=buyer)
        self.__orders.append(order)
        logging.info(f"Order {order.id} created by '{buyer.name}'.")
        return order

    def add_ticket_to_order(self, order_id: int, ticket: Ticket) -> bool:
        order = self.get_order_by_id(order_id)
        if order:
            order.add_ticket(ticket)
            return True
        return False

    def complete_order(self, order_id: int) -> bool:
        order = self.get_order_by_id(order_id)
        if order:
            return order.complete_order()
        return False

    def cancel_order(self, order_id: int) -> bool:
        order = self.get_order_by_id(order_id)
        if order:
            return order.cancel_order()
        return False

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        for order in self.__orders:
            if order.id == order_id:
                return order
        logging.warning(f"Order with ID {order_id} not found.")
        return None

    def display_order_tickets(self, order_id: int):
        order = self.get_order_by_id(order_id)
        if order:
            order.display_order_tickets()
        else:
            logging.error(f"Order with ID {order_id} not found.")

    # Payment Management
    def process_payment(self, order_id: int, success: bool) -> bool:
        order = self.get_order_by_id(order_id)
        if order:
            payment = Payment(order=order, amount=order.total_price)
            self.__payments.append(payment)
            return payment.process_payment(success=success)
        return False

    # Refund Management
    def create_refund_request(self, ticket_id: int, buyer: User) -> Optional[RefundRequest]:
        ticket = self.get_ticket_by_id(ticket_id)
        if ticket:
            refund_request = RefundRequest(ticket=ticket, buyer=buyer)
            self.__refund_requests.append(refund_request)
            logging.info(f"Refund request {refund_request.id} created for ticket {ticket_id}.")
            return refund_request
        return None

    def approve_refund(self, refund_request_id: int) -> bool:
        refund_request = self.get_refund_request_by_id(refund_request_id)
        if refund_request:
            return refund_request.approve_refund()
        return False

    def reject_refund(self, refund_request_id: int) -> bool:
        refund_request = self.get_refund_request_by_id(refund_request_id)
        if refund_request:
            return refund_request.reject_refund()
        return False

    def get_refund_request_by_id(self, refund_request_id: int) -> Optional[RefundRequest]:
        for refund_request in self.__refund_requests:
            if refund_request.id == refund_request_id:
                return refund_request
        logging.warning(f"Refund request with ID {refund_request_id} not found.")
        return None

    # Helper Methods
    def get_ticket_by_id(self, ticket_id: int) -> Optional[Ticket]:
        for event in self.__events:
            for zone in event.zones.values():
                for ticket in zone.tickets:
                    if ticket.id == ticket_id:
                        return ticket
        logging.warning(f"Ticket with ID {ticket_id} not found.")
        return None

    def purchase_tickets(self, order_id: int, zone: Zone, quantity: int) -> bool:
        order = self.get_order_by_id(order_id)
        if not order:
            logging.error(f"Order with ID {order_id} not found.")
            return False

        available_tickets = zone.get_available_tickets(quantity)
        if len(available_tickets) < quantity:
            logging.error(f"Not enough tickets available in zone '{zone.type}'.")
            return False

        for ticket in available_tickets:
            if ticket.purchase(order.buyer):
                self.add_ticket_to_order(order_id=order.id, ticket=ticket)
                self.add_ticket_to_user(user=order.buyer, ticket=ticket)
        
        logging.info(f"Purchased {quantity} tickets in zone '{zone.type}' for order {order_id}.")
        return True

    def add_zones_to_event(self, event: Event, zones: List[Dict[str, float]], user: User) -> bool:
        for zone in zones:
            if not self.add_zone_to_event(event_id=event.id, zone_type=zone['type'], percentage=zone['percentage'], price=zone['price'], user=user):
                logging.error(f"Failed to add zone '{zone['type']}' to event '{event.name}'.")
                return False
        return True

    def add_hall(self, hall: Hall):
        self.__halls.append(hall)

    def get_halls(self) -> List[Hall]:
        return self.__halls

    def get_hall_by_id(self, hall_id: int) -> Optional[Hall]:
        for hall in self.__halls:
            if hall.id == hall_id:
                return hall
        logging.warning(f"Hall with ID {hall_id} not found.")
        return None

# Example Usage
if __name__ == "__main__":
    controller = Controller()

    # Create a user with multiple roles
    user = controller.create_user(name="John Doe", email="john@example.com", password="password123", roles=["Buyer", "EventOrganizer"])

    # Create a hall
    hall_1_large = Hall(size="Large", capacity=1000)
    hall_2_medium = Hall(size="Medium", capacity=500)
    hall_3_small = Hall(size="Small", capacity=200)

    # Create events with zones
    event_1 = controller.create_event(
        name="Concert",
        date=datetime(2023, 8, 15),
        organizer=user,
        hall=hall_1_large,
        zones=[
            {"type": "VIP", "percentage": 0.2, "price": 150.0},
            {"type": "Regular", "percentage": 0.8, "price": 50.0}
        ]
    )
    event_2 = controller.create_event(
        name="Theatre Play",
        date=datetime(2023, 9, 20),
        organizer=user,
        hall=hall_2_medium,
        zones=[
            {"type": "VIP", "percentage": 0.1, "price": 100.0},
            {"type": "Regular", "percentage": 0.9, "price": 30.0}
        ]
    )
    event_3 = controller.create_event(
        name="Conference",
        date=datetime(2023, 10, 25),
        organizer=user,
        hall=hall_3_small,
        zones=[
            {"type": "Regular", "percentage": 1.0, "price": 20.0}
        ]
    )

    # Display event info before purchasing tickets
    print("\nDisplaying Event Info (Before Purchasing Tickets):")
    controller.display_event_info(event_id=event_1.id)

    # Purchase some tickets
    vip_zone = event_1.zones["VIP"]
    regular_zone = event_1.zones["Regular"]

    # Create an order
    order = controller.create_order(buyer=user)

    # Purchase 50 VIP tickets
    controller.purchase_tickets(order_id=order.id, zone=vip_zone, quantity=50)

    # Purchase 100 Regular tickets
    controller.purchase_tickets(order_id=order.id, zone=regular_zone, quantity=100)

    # Complete the order
    controller.complete_order(order_id=order.id)

    # Display order tickets
    print("\nDisplaying Order Tickets:")
    controller.display_order_tickets(order_id=order.id)

    # Display event info after purchasing tickets
    print("\nDisplaying Event Info (After Purchasing Tickets):")
    controller.display_event_info(event_id=event_1.id)

    # Test purchasing all remaining tickets in VIP zone
    order_2 = controller.create_order(buyer=user)
    controller.purchase_tickets(order_id=order_2.id, zone=vip_zone, quantity=60)
    controller.complete_order(order_id=order_2.id)

    # Display order tickets
    print("\nDisplaying Order Tickets (Order 2):")
    controller.display_order_tickets(order_id=order_2.id)

    # Display event info after purchasing all VIP tickets
    print("\nDisplaying Event Info (After Purchasing All VIP Tickets):")
    controller.display_event_info(event_id=event_1.id)

    # Test purchasing tickets when no tickets are available
    order_3 = controller.create_order(buyer=user)
    success = controller.purchase_tickets(order_id=order_3.id, zone=vip_zone, quantity=1)
    if not success:
        print("\nNo VIP tickets available for purchase.")
    controller.complete_order(order_id=order_3.id)

    # Display order tickets
    print("\nDisplaying Order Tickets (Order 3):")
    controller.display_order_tickets(order_id=order_3.id)

    # Display final event info
    print("\nDisplaying Final Event Info:")
    controller.display_event_info(event_id=event_1.id)

    # Display user tickets
    print("\nDisplaying User Tickets:")
    controller.display_user_tickets(user_id=user.id)