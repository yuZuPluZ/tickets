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