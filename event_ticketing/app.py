from fasthtml.common import *
from datetime import datetime
from controller import *

app, rt = fast_app()

# Initialize the controller and create sample data
controller = Controller()
user = controller.create_user(name="John Doe", email="john@example.com", password="password123", roles=["Buyer", "EventOrganizer"])
hall1 = Hall(size="Large", capacity=1000)
hall2 = Hall(size="Large", capacity=1000)
hall3 = Hall(size="Large", capacity=1000)
hall4 = Hall(size="Large", capacity=1000)
hall5 = Hall(size="small", capacity=500)
controller.add_hall(hall1)
controller.add_hall(hall2)
controller.add_hall(hall3)
controller.add_hall(hall4)
controller.add_hall(hall5)
event = controller.create_event(
    name="Concert",
    date=datetime(2023, 8, 15),
    organizer=user,
    hall=hall1,
    zones=[
        {"type": "VIP", "percentage": 0.2, "price": 150.0},
        {"type": "Regular", "percentage": 0.8, "price": 50.0}
    ]
)
event1 = controller.create_event(
    name="Concert2",
    date=datetime(2023, 8, 15),
    organizer=user,
    hall=hall2,
    zones=[
        {"type": "VIP", "percentage": 0.2, "price": 150.0},
        {"type": "Regular", "percentage": 0.8, "price": 50.0}
    ]
)

# Routes
@rt("/")
def home():
    """Home page with links to events and user tickets."""
    return Titled("Welcome", 
        Ul(
            Li(A(href="/events")("View Events")),
            Li(A(href="/user_tickets")("My Tickets")),
            Li(A(href="/create_event")("Create Event")),
            Li(A(href="/login")("Login")),
            Li(A(href="/register")("Register"))
        )
    )

@rt("/events")
def list_events():
    """List all events."""
    events = controller.get_events()  # Use a getter method
    event_list = Ul(*[
        Li(A(href=f"/event/{event.id}")(f"{event.name} - {event.date.strftime('%Y-%m-%d')}"))
        for event in events
    ])
    return Titled("Events", event_list)

@rt("/event/{event_id:int}")
def event_detail(event_id: int):
    """Display details of a specific event."""
    event = controller.get_event_by_id(event_id)
    if not event:
        return Titled("Error", P("Event not found"))
    
    zones_info = Ul(*[
        Li(
            f"{zone_type} - ${zone.price} ({zone.get_available_tickets_count()} available)",
            Form(method="post", action=f"/purchase_tickets/{event.id}/{zone_type}")(
                Input(type="number", name="quantity", min="1", max=str(zone.get_available_tickets_count()), required=True),
                Button("Buy Tickets", type="submit")
            )
        ) for zone_type, zone in event.zones.items()
    ])
    
    return Titled(event.name, 
        P(f"Date: {event.date.strftime('%Y-%m-%d %H:%M:%S')}"),
        H2("Zones"),
        zones_info
    )

@rt("/purchase_tickets/{event_id:int}/{zone_type}", methods=["POST"])
async def purchase_tickets(req, event_id: int, zone_type: str):
    """Handle ticket purchases."""
    event = controller.get_event_by_id(event_id)
    if not event:
        return Titled("Error", P("Event not found"))
    
    zone = event.zones.get(zone_type)
    if not zone:
        return Titled("Error", P("Zone not found"))
    
    form = await req.form()
    quantity = int(form.get("quantity", 0))  # Use req.form instead of app.request
    if quantity <= 0:
        return Titled("Error", P("Invalid quantity"))

    order = controller.create_order(buyer=user)
    success = controller.purchase_tickets(order_id=order.id, zone=zone, quantity=quantity)
    if not success:
        return Titled("Error", P("Failed to purchase tickets"))
    
    controller.complete_order(order_id=order.id)
    return Titled("Success", 
        P(f"Order ID: {order.id}"),
        P(f"Quantity: {quantity}"),
        P(f"Zone: {zone_type}"),
        A(href="/user_tickets")("View My Tickets")
    )

@rt("/user_tickets")
def user_tickets():
    """Display tickets owned by the user."""
    user_tickets = controller.get_user_tickets(user.id)  # Use getter instead of accessing private variables
    tickets_list = Ul(*[
        Li(f"Ticket ID: {ticket.id}, Event: {ticket.zone.event.name}, Zone: {ticket.zone.type}, Status: {ticket.status.name}")
        for ticket in user_tickets
    ])
    return Titled("My Tickets", tickets_list)

@rt("/create_event", methods=["GET", "POST"])
async def create_event(req):
    """Create a new event."""
    if req.method == "POST":
        form = await req.form()
        name = form.get("name")
        date = form.get("date")
        hall_id = int(form.get("hall_id"))
        zones = [
            {"type": "VIP", "percentage": float(form.get("vip_percentage")), "price": float(form.get("vip_price"))},
            {"type": "Regular", "percentage": float(form.get("regular_percentage")), "price": float(form.get("regular_price"))}
        ]

        hall = controller.get_hall_by_id(hall_id)
        event = controller.create_event(
            name=name,
            date=datetime.strptime(date, "%Y-%m-%d"),
            organizer=user,
            hall=hall,
            zones=zones
        )
        return Titled("Event Created", P(f"Event '{event.name}' created successfully!"))

    halls = controller.get_halls()
    hall_options = [Option(value=hall.id)(f"{hall.size} - Capacity: {hall.capacity}") for hall in halls]

    return Titled("Create Event",
        Form(method="post")(
            P("Event Name: ", Input(type="text", name="name", required=True)),
            P("Event Date: ", Input(type="date", name="date", required=True)),
            P("Hall: ", Select(name="hall_id", required=True)(*hall_options)),
            P("VIP Zone Percentage: ", Input(type="number", name="vip_percentage", step="0.01", required=True)),
            P("VIP Zone Price: ", Input(type="number", name="vip_price", step="0.01", required=True)),
            P("Regular Zone Percentage: ", Input(type="number", name="regular_percentage", step="0.01", required=True)),
            P("Regular Zone Price: ", Input(type="number", name="regular_price", step="0.01", required=True)),
            Button("Create Event", type="submit")
        )
    )

@rt("/login", methods=["GET", "POST"])
async def login(req):
    """User login."""
    if req.method == "POST":
        form = await req.form()
        email = form.get("email")
        password = form.get("password")
        user = controller.authenticate_user(email, password)
        if user:
            return Titled("Login Successful", P(f"Welcome, {user.name}!"))
        else:
            return Titled("Login Failed", P("Invalid email or password."))

    return Titled("Login",
        Form(method="post")(
            P("Email: ", Input(type="email", name="email", required=True)),
            P("Password: ", Input(type="password", name="password", required=True)),
            Button("Login", type="submit")
        )
    )

@rt("/register", methods=["GET", "POST"])
async def register(req):
    """User registration."""
    if req.method == "POST":
        form = await req.form()
        name = form.get("name")
        email = form.get("email")
        password = form.get("password")
        roles = ["Buyer"]  # Default role
        user = controller.create_user(name=name, email=email, password=password, roles=roles)
        return Titled("Registration Successful", P(f"User '{user.name}' registered successfully!"))

    return Titled("Register",
        Form(method="post")(
            P("Name: ", Input(type="text", name="name", required=True)),
            P("Email: ", Input(type="email", name="email", required=True)),
            P("Password: ", Input(type="password", name="password", required=True)),
            Button("Register", type="submit")
        )
    )

serve()
