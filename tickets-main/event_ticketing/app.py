from fasthtml.common import *
from datetime import datetime
from controller import *
import hashlib
from fastapi.responses import RedirectResponse
import shutil  # Add this import

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
    description="A grand concert featuring popular artists.",
    image_url="https://example.com/concert.jpg",
    zones=[ 
        {"type": "VIP", "percentage": 0.2, "price": 150.0, "quantity": int(hall1.capacity * 0.2)},
        {"type": "Regular", "percentage": 0.8, "price": 50.0, "quantity": int(hall1.capacity * 0.8)}
    ]
)
event1 = controller.create_event(
    name="Concert2",
    date=datetime(2023, 8, 15),
    organizer=user,
    hall=hall2,
    description="Another amazing concert with different artists.",
    image_url="https://example.com/concert2.jpg",
    zones=[
        {"type": "VIP", "percentage": 0.2, "price": 150.0, "quantity": int(hall2.capacity * 0.2)},
        {"type": "Regular", "percentage": 0.8, "price": 50.0, "quantity": int(hall2.capacity * 0.8)}
    ]
)

# Session management
sessions = {}

def get_current_user(req):
    session_id = req.cookies.get("session_id")
    if (session_id and session_id in sessions):
        return sessions[session_id]
    return None

# Routes
@rt("/")
def home(req):
    """Home page with links to events and user tickets."""
    current_user = get_current_user(req)
    user_info = P(f"Logged in as: {current_user.name}") if current_user else P("Not logged in")
    return Titled("Welcome", 
        Ul(
            Li(A(href="/events")("View Events")),
            Li(A(href="/user_tickets")("My Tickets")),
            Li(A(href="/create_event")("Create Event")),
            Li(A(href="/login")("Login")),
            Li(A(href="/register")("Register")),
            Li(A(href="/logout")("Logout")) if current_user else ""
        ),
        user_info
    )

@rt("/events")
def list_events():
    """List all events."""
    events = controller.get_events()  # Use a getter method
    event_cards = Div(*[
        Div(Class="card")(
            Img(src=f"/{event.image_url}", Class="card-img-top", alt=event.name),
            Div(Class="card-body")(
                H5(Class="card-title")(event.name),
                P(Class="card-text")(f"Date: {event.date.strftime('%Y-%m-%d')}"),
                P(Class="card-text")(event.description),
                A(href=f"/event/{event.id}", Class="btn btn-primary")("View Details")
            )
        ) for event in events
    ])
    return Titled("Events", event_cards)

@rt("/event/{event_id:int}")
def event_detail(event_id: int):
    """Display details of a specific event."""
    event = controller.get_event_by_id(event_id)
    if not event:
        return Titled("Error", P("Event not found"))
    
    zones_info = Ul(*[
        Li(
            f"{zone_type} - ${zone.price} ({zone.get_available_tickets_count()} available)"
        ) for zone_type, zone in event.zones.items()
    ])
    
    vip_zone = event.zones.get("VIP")
    regular_zone = event.zones.get("Regular")
    vip_sold_out = vip_zone.get_available_tickets_count() == 0 if vip_zone else True
    regular_sold_out = regular_zone.get_available_tickets_count() == 0 if regular_zone else True
    
    return Titled(event.name, 
        P(f"Date: {event.date.strftime('%Y-%m-%d %H:%M:%S')}"),
        P(f"Description: {event.description}"),
        Img(src=f"/{event.image_url}", alt=event.name),
        H2("Zones"),
        zones_info,
        Form(method="post", action=f"/purchase_tickets/{event.id}")(
            P("VIP Quantity: ", Input(type="number", name="vip_quantity", min="0", required=True, disabled=vip_sold_out)),
            P("Regular Quantity: ", Input(type="number", name="regular_quantity", min="0", required=True, disabled=regular_sold_out)),
            Button("Buy Tickets", type="submit", disabled=vip_sold_out and regular_sold_out)
        )
    )

@rt("/purchase_tickets/{event_id:int}", methods=["POST"])
async def purchase_tickets(req, event_id: int):
    """Handle ticket purchases."""
    event = controller.get_event_by_id(event_id)
    if not event:
        return Titled("Error", P("Event not found"))
    
    form = await req.form()
    vip_quantity = int(form.get("vip_quantity", 0))
    regular_quantity = int(form.get("regular_quantity", 0))
    
    if vip_quantity <= 0 and regular_quantity <= 0:
        return Titled("Error", P("Invalid quantity"))

    vip_zone = event.zones.get("VIP")
    regular_zone = event.zones.get("Regular")
    vip_error = regular_error = None

    if vip_quantity > 0 and vip_zone and vip_quantity > vip_zone.get_available_tickets_count():
        vip_error = "Not enough VIP tickets available"

    if regular_quantity > 0 and regular_zone and regular_quantity > regular_zone.get_available_tickets_count():
        regular_error = "Not enough Regular tickets available"

    if vip_error or regular_error:
        return Titled("Error", 
            P(vip_error) if vip_error else "",
            P(regular_error) if regular_error else "",
            A(href=f"/event/{event.id}")("Go Back")
        )

    current_user = get_current_user(req)
    if not current_user:
        return Titled("Error", P("User not logged in"))

    order = controller.create_order(buyer=current_user)
    success_vip = success_regular = True

    if vip_quantity > 0:
        success_vip = controller.purchase_tickets(order_id=order.id, zone=vip_zone, quantity=vip_quantity)

    if regular_quantity > 0:
        success_regular = controller.purchase_tickets(order_id=order.id, zone=regular_zone, quantity=regular_quantity)

    if not success_vip and not success_regular:
        return Titled("Error", P("Failed to purchase tickets"))

    controller.complete_order(order_id=order.id)
    return Titled("Success", 
        P(f"Order ID: {order.id}"),
        P(f"VIP Quantity: {vip_quantity}"),
        P(f"Regular Quantity: {regular_quantity}"),
        A(href="/user_tickets")("View My Tickets")
    )

@rt("/user_tickets")
def user_tickets(req):
    """Display tickets owned by the user."""
    current_user = get_current_user(req)
    if not current_user:
        return Titled("Error", P("User not logged in"))
    
    user_tickets = controller.get_user_tickets(current_user.id)
    if not user_tickets:
        return Titled("My Tickets", P("No tickets found."))

    tickets_list = Ul(*[
        Li(
            f"Ticket ID: {ticket.id}, Event: {ticket.zone.event.name}, Zone: {ticket.zone.type}",
            Form(method="post", action=f"/request_refund/{ticket.id}")(
                Button("Request Refund", type="submit", disabled=ticket.status != TicketStatus.SOLD)
            )
        ) for ticket in user_tickets
    ])
    return Titled("My Tickets", tickets_list)

@rt("/create_event", methods=["GET", "POST"])
async def create_event(req):
    """Create a new event."""
    if req.method == "POST":
        form = await req.form()
        name = form.get("name")
        date = form.get("date")
        description = form.get("description")
        image_file = form.get("image_file")
        hall_id = int(form.get("hall_id"))
        hall = controller.get_hall_by_id(hall_id)
        zones = [
            {"type": "VIP", "percentage": float(form.get("vip_percentage")), "price": float(form.get("vip_price")), "quantity": int(hall.capacity * float(form.get("vip_percentage")) / 100)},
            {"type": "Regular", "percentage": float(form.get("regular_percentage")), "price": float(form.get("regular_price")), "quantity": int(hall.capacity * float(form.get("regular_percentage")) / 100)}
        ]

        # Ensure the directory exists
        image_dir = "static/images"
        shutil.os.makedirs(image_dir, exist_ok=True)

        # Save the uploaded image file
        image_url = shutil.os.path.join(image_dir, image_file.filename)
        with open(image_url, "wb") as f:
            f.write(image_file.file.read())

        event = controller.create_event(
            name=name,
            date=datetime.strptime(date, "%Y-%m-%d"),
            organizer=user,
            hall=hall,
            description=description,
            image_url=image_url,
            zones=zones
        )
        return Titled("Event Created", P(f"Event '{event.name}' created successfully!"))

    halls = controller.get_halls()
    used_halls = {event.hall.id for event in controller.get_events()}
    available_halls = [hall for hall in halls if hall.id not in used_halls]
    hall_options = [Option(value=hall.id)(f"ID: {hall.id} - {hall.size} - Capacity: {hall.capacity}") for hall in available_halls]

    return Titled("Create Event",
        Form(method="post", enctype="multipart/form-data")(
            P("Event Name: ", Input(type="text", name="name", required=True)),
            P("Event Date: ", Input(type="date", name="date", required=True)),
            P("Description: ", Textarea(name="description", required=True)),
            P("Image File: ", Input(type="file", name="image_file", accept="image/*", required=True)),
            P("Hall: ", Select(name="hall_id", required=True)(*hall_options)),
            P("VIP Zone Percentage: ", Input(type="number", name="vip_percentage", step="0.01", required=True)),
            P("VIP Zone Price: ", Input(type="number", name="vip_price", step="0.01", required=True)),
            P("Regular Zone Percentage: ", Input(type="number", name="regular_percentage", step="0.01", required=True)),
            P("Regular Zone Price: ", Input(type="number", name="regular_price", step="0.01", required=True)),
            Button("Create Event", type="submit")
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
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        user = controller.create_user(name=name, email=email, password=hashed_password, roles=["Buyer"])
        return Titled("Registration Successful", P(f"User '{user.name}' registered successfully!"))

    return Titled("Register",
        Form(method="post")(
            P("Name: ", Input(type="text", name="name", required=True)),
            P("Email: ", Input(type="email", name="email", required=True)),
            P("Password: ", Input(type="password", name="password", required=True)),
            Button("Register", type="submit")
        )
    )

@rt("/login", methods=["GET", "POST"])
async def login(req):
    """User login."""
    if req.method == "POST":
        form = await req.form()
        email = form.get("email")
        password = form.get("password")
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        user = controller.authenticate_user(email=email, password=hashed_password)
        if user:
            session_id = hashlib.sha256(f"{user.id}{datetime.now()}".encode()).hexdigest()
            sessions[session_id] = user
            res = RedirectResponse(url="/")
            res.set_cookie("session_id", session_id)
            return res
        return Titled("Login Failed", P("Invalid email or password"))

    return Titled("Login",
        Form(method="post")(
            P("Email: ", Input(type="email", name="email", required=True)),
            P("Password: ", Input(type="password", name="password", required=True)),
            Button("Login", type="submit")
        )
    )

@rt("/logout")
def logout(req):
    """User logout."""
    session_id = req.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    res = RedirectResponse(url="/")
    res.delete_cookie("session_id")
    return res

@rt("/request_refund/{ticket_id:int}", methods=["POST"])
def request_refund(req, ticket_id: int):
    """Handle refund requests."""
    current_user = get_current_user(req)
    if not current_user:
        return Titled("Error", P("User not logged in"))

    ticket = controller.get_ticket_by_id(ticket_id)
    if not ticket or ticket.status != TicketStatus.SOLD or ticket.zone.event.date > datetime.now():
        return Titled("Error", P("Invalid ticket for refund"))

    refund_request = controller.create_refund_request(ticket_id=ticket_id, buyer=current_user)
    if refund_request:
        controller.approve_refund(refund_request.id)  # Automatically approve the refund request
        return Titled("Refund Requested", P(f"Refund request for ticket ID {ticket_id} has been submitted and approved."))
    return Titled("Error", P("Failed to create refund request"))

@rt("/refund_requests")
def list_refund_requests(req):
    """List all refund requests."""
    current_user = get_current_user(req)
    if not current_user or not current_user.has_role("EventOrganizer"):
        return Titled("Error", P("Access denied"))

    refund_requests = controller.get_refund_requests()
    if not refund_requests:
        return Titled("Refund Requests", P("No refund requests found."))

    requests_list = Ul(*[
        Li(f"Refund Request ID: {request.id}, Ticket ID: {request.ticket.id}, Status: {request.status.name}")
        for request in refund_requests
    ])
    return Titled("Refund Requests", requests_list)

@rt("/approve_refund/{refund_request_id:int}", methods=["POST"])
def approve_refund(req, refund_request_id: int):
    """Approve a refund request."""
    current_user = get_current_user(req)
    if not current_user or not current_user.has_role("EventOrganizer"):
        return Titled("Error", P("Access denied"))

    success = controller.approve_refund(refund_request_id=refund_request_id)
    if success:
        return Titled("Success", P(f"Refund request ID {refund_request_id} approved."))
    return Titled("Error", P("Failed to approve refund request"))

@rt("/reject_refund/{refund_request_id:int}", methods=["POST"])
def reject_refund(req, refund_request_id: int):
    """Reject a refund request."""
    current_user = get_current_user(req)
    if not current_user or not current_user.has_role("EventOrganizer"):
        return Titled("Error", P("Access denied"))

    success = controller.reject_refund(refund_request_id=refund_request_id)
    if success:
        return Titled("Success", P(f"Refund request ID {refund_request_id} rejected."))
    return Titled("Error", P("Failed to reject refund request"))

serve()
