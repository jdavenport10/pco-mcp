import asyncio

from uncalled_for import Depends
from pypco import PCO

from server import mcp, get_pco, _build_patch_body


# =============================================================================
# Registration Event Operations
# =============================================================================

@mcp.tool()
async def get_registration_events(filter: str = "unarchived", pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of registration events from Planning Center Online.

    Args:
        filter (str, optional): Filter for events. Common values: "unarchived", "unarchived,published".
            Defaults to "unarchived".

    Returns:
        list: A list of registration event data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/registrations/v2/events?filter={filter}&order=starts_at"
    )
    return response["data"]

@mcp.tool()
async def get_registration_event(event_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific registration event.

    Args:
        event_id (str): The ID of the registration event.

    Returns:
        dict: The registration event data.
    """
    response = await asyncio.to_thread(pco.get, f"/registrations/v2/events/{event_id}")
    return response["data"]

@mcp.tool()
async def create_registration_event(
    name: str,
    description: str = None,
    starts_at: str = None,
    ends_at: str = None,
    featured: bool = None,
    registration_state: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new registration event in Planning Center Online.

    Args:
        name (str): The name of the event.
        description (str, optional): A description of the event.
        starts_at (str, optional): The start time in ISO 8601 format (e.g., "2025-06-01T09:00:00Z").
        ends_at (str, optional): The end time in ISO 8601 format (e.g., "2025-06-01T17:00:00Z").
        featured (bool, optional): Whether the event is featured.
        registration_state (str, optional): The registration state (e.g., "published", "draft").

    Returns:
        dict: The created registration event data.
    """
    attributes = {"name": name}
    if description is not None:
        attributes["description"] = description
    if starts_at is not None:
        attributes["starts_at"] = starts_at
    if ends_at is not None:
        attributes["ends_at"] = ends_at
    if featured is not None:
        attributes["featured"] = featured
    if registration_state is not None:
        attributes["registration_state"] = registration_state

    body = pco.template("Event", attributes)
    response = await asyncio.to_thread(pco.post, "/registrations/v2/events", body)
    return response["data"]

@mcp.tool()
async def update_registration_event(
    event_id: str,
    name: str = None,
    description: str = None,
    starts_at: str = None,
    ends_at: str = None,
    featured: bool = None,
    registration_state: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing registration event in Planning Center Online.

    Args:
        event_id (str): The ID of the event to update.
        name (str, optional): The new name for the event.
        description (str, optional): The new description.
        starts_at (str, optional): The new start time in ISO 8601 format.
        ends_at (str, optional): The new end time in ISO 8601 format.
        featured (bool, optional): Whether the event is featured.
        registration_state (str, optional): The new registration state.

    Returns:
        dict: The updated registration event data.
    """
    body = _build_patch_body(
        "Event",
        name=name,
        description=description,
        starts_at=starts_at,
        ends_at=ends_at,
        featured=featured,
        registration_state=registration_state,
    )
    response = await asyncio.to_thread(pco.patch, f"/registrations/v2/events/{event_id}", body)
    return response["data"]

@mcp.tool()
async def delete_registration_event(event_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a registration event from Planning Center Online.

    Args:
        event_id (str): The ID of the event to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/registrations/v2/events/{event_id}")
    return {"success": True, "message": f"Registration event {event_id} deleted successfully."}


# =============================================================================
# Event Category Operations
# =============================================================================

@mcp.tool()
async def get_event_categories(event_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of categories for a specific registration event.

    Categories define registration types (e.g., leader, volunteer, child, adult).

    Args:
        event_id (str): The ID of the registration event.

    Returns:
        list: A list of event category data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/registrations/v2/events/{event_id}/event_categories"
    )
    return response["data"]

@mcp.tool()
async def create_event_category(
    event_id: str,
    name: str,
    description: str = None,
    capacity: int = None,
    position: int = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new category for a registration event.

    Args:
        event_id (str): The ID of the registration event.
        name (str): The name of the category (e.g., "Adult", "Child", "Leader").
        description (str, optional): A description of the category.
        capacity (int, optional): The maximum number of registrants for this category.
        position (int, optional): The display order position.

    Returns:
        dict: The created event category data.
    """
    attributes = {"name": name}
    if description is not None:
        attributes["description"] = description
    if capacity is not None:
        attributes["capacity"] = capacity
    if position is not None:
        attributes["position"] = position

    body = pco.template("EventCategory", attributes)
    response = await asyncio.to_thread(
        pco.post,
        f"/registrations/v2/events/{event_id}/event_categories",
        body,
    )
    return response["data"]

@mcp.tool()
async def update_event_category(
    event_id: str,
    category_id: str,
    name: str = None,
    description: str = None,
    capacity: int = None,
    position: int = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing category for a registration event.

    Args:
        event_id (str): The ID of the registration event.
        category_id (str): The ID of the category to update.
        name (str, optional): The new name for the category.
        description (str, optional): The new description.
        capacity (int, optional): The new maximum capacity.
        position (int, optional): The new display order position.

    Returns:
        dict: The updated event category data.
    """
    body = _build_patch_body(
        "EventCategory",
        name=name,
        description=description,
        capacity=capacity,
        position=position,
    )
    response = await asyncio.to_thread(
        pco.patch,
        f"/registrations/v2/events/{event_id}/event_categories/{category_id}",
        body,
    )
    return response["data"]

@mcp.tool()
async def delete_event_category(event_id: str, category_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a category from a registration event.

    Args:
        event_id (str): The ID of the registration event.
        category_id (str): The ID of the category to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(
        pco.delete,
        f"/registrations/v2/events/{event_id}/event_categories/{category_id}",
    )
    return {"success": True, "message": f"Event category {category_id} deleted successfully."}


# =============================================================================
# Event Time Operations
# =============================================================================

@mcp.tool()
async def get_event_times(event_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of times for a specific registration event.

    Args:
        event_id (str): The ID of the registration event.

    Returns:
        list: A list of event time data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/registrations/v2/events/{event_id}/event_times"
    )
    return response["data"]

@mcp.tool()
async def create_event_time(
    event_id: str,
    starts_at: str,
    ends_at: str,
    name: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new time slot for a registration event.

    Args:
        event_id (str): The ID of the registration event.
        starts_at (str): The start time in ISO 8601 format (e.g., "2025-06-01T09:00:00Z").
        ends_at (str): The end time in ISO 8601 format (e.g., "2025-06-01T17:00:00Z").
        name (str, optional): A name for this time slot.

    Returns:
        dict: The created event time data.
    """
    attributes = {"starts_at": starts_at, "ends_at": ends_at}
    if name is not None:
        attributes["name"] = name

    body = pco.template("EventTime", attributes)
    response = await asyncio.to_thread(
        pco.post,
        f"/registrations/v2/events/{event_id}/event_times",
        body,
    )
    return response["data"]

@mcp.tool()
async def update_event_time(
    event_id: str,
    event_time_id: str,
    starts_at: str = None,
    ends_at: str = None,
    name: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing time slot for a registration event.

    Args:
        event_id (str): The ID of the registration event.
        event_time_id (str): The ID of the event time to update.
        starts_at (str, optional): The new start time in ISO 8601 format.
        ends_at (str, optional): The new end time in ISO 8601 format.
        name (str, optional): The new name for this time slot.

    Returns:
        dict: The updated event time data.
    """
    body = _build_patch_body("EventTime", starts_at=starts_at, ends_at=ends_at, name=name)
    response = await asyncio.to_thread(
        pco.patch,
        f"/registrations/v2/events/{event_id}/event_times/{event_time_id}",
        body,
    )
    return response["data"]

@mcp.tool()
async def delete_event_time(event_id: str, event_time_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a time slot from a registration event.

    Args:
        event_id (str): The ID of the registration event.
        event_time_id (str): The ID of the event time to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(
        pco.delete,
        f"/registrations/v2/events/{event_id}/event_times/{event_time_id}",
    )
    return {"success": True, "message": f"Event time {event_time_id} deleted successfully."}


# =============================================================================
# Attendee Operations
# =============================================================================

@mcp.tool()
async def get_event_attendees(event_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of attendees for a specific registration event.

    Args:
        event_id (str): The ID of the registration event.

    Returns:
        list: A list of attendee data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/registrations/v2/events/{event_id}/attendees"
    )
    return response["data"]

@mcp.tool()
async def get_event_attendee(event_id: str, attendee_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific attendee of a registration event.

    Args:
        event_id (str): The ID of the registration event.
        attendee_id (str): The ID of the attendee.

    Returns:
        dict: The attendee data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/registrations/v2/events/{event_id}/attendees/{attendee_id}"
    )
    return response["data"]

@mcp.tool()
async def create_event_attendee(
    event_id: str,
    person_id: str,
    category_id: str = None,
    status: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Add an attendee to a registration event.

    Args:
        event_id (str): The ID of the registration event.
        person_id (str): The ID of the person to add as an attendee.
        category_id (str, optional): The ID of the event category to register under.
        status (str, optional): The attendee status.

    Returns:
        dict: The created attendee data.
    """
    attributes = {}
    if status is not None:
        attributes["status"] = status

    body = {
        "data": {
            "type": "Attendee",
            "attributes": attributes,
            "relationships": {
                "person": {
                    "data": {"type": "Person", "id": person_id}
                }
            }
        }
    }

    if category_id is not None:
        body["data"]["relationships"]["event_category"] = {
            "data": {"type": "EventCategory", "id": category_id}
        }

    response = await asyncio.to_thread(
        pco.post,
        f"/registrations/v2/events/{event_id}/attendees",
        body,
    )
    return response["data"]

@mcp.tool()
async def update_event_attendee(
    event_id: str,
    attendee_id: str,
    status: str = None,
    category_id: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing attendee on a registration event.

    Args:
        event_id (str): The ID of the registration event.
        attendee_id (str): The ID of the attendee to update.
        status (str, optional): The new attendee status.
        category_id (str, optional): The ID of the new event category.

    Returns:
        dict: The updated attendee data.
    """
    body = _build_patch_body("Attendee", status=status)

    if category_id is not None:
        body["data"]["relationships"] = {
            "event_category": {
                "data": {"type": "EventCategory", "id": category_id}
            }
        }

    response = await asyncio.to_thread(
        pco.patch,
        f"/registrations/v2/events/{event_id}/attendees/{attendee_id}",
        body,
    )
    return response["data"]

@mcp.tool()
async def delete_event_attendee(event_id: str, attendee_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Remove an attendee from a registration event.

    Args:
        event_id (str): The ID of the registration event.
        attendee_id (str): The ID of the attendee to remove.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(
        pco.delete,
        f"/registrations/v2/events/{event_id}/attendees/{attendee_id}",
    )
    return {"success": True, "message": f"Attendee {attendee_id} removed successfully."}


# =============================================================================
# Event Duplication
# =============================================================================

@mcp.tool()
async def duplicate_registration_event(event_id: str, new_name: str = None, pco: PCO = Depends(get_pco)) -> dict:
    """
    Duplicate a registration event, including its categories and event times.

    This creates a full copy of an event. If a new_name is not provided,
    the copy will be named "<original name> (Copy)".

    Args:
        event_id (str): The ID of the event to duplicate.
        new_name (str, optional): A name for the duplicated event. Defaults to "<name> (Copy)".

    Returns:
        dict: The duplicated event data including copied sub-resources.
    """
    # Fetch the source event
    source_response = await asyncio.to_thread(pco.get, f"/registrations/v2/events/{event_id}")
    source_event = source_response["data"]
    source_attrs = source_event["attributes"]

    # Build attributes for the new event
    copy_name = new_name if new_name else f"{source_attrs.get('name', 'Event')} (Copy)"
    new_attrs = {"name": copy_name}
    for attr in ["description", "starts_at", "ends_at", "featured", "registration_state"]:
        if source_attrs.get(attr) is not None:
            new_attrs[attr] = source_attrs[attr]

    # Create the new event
    body = pco.template("Event", new_attrs)
    new_event_response = await asyncio.to_thread(pco.post, "/registrations/v2/events", body)
    new_event = new_event_response["data"]
    new_event_id = new_event["id"]

    copied_categories = []
    copied_times = []

    # Copy categories
    try:
        categories_response = await asyncio.to_thread(
            pco.get,
            f"/registrations/v2/events/{event_id}/event_categories"
        )
        for cat in categories_response.get("data", []):
            cat_attrs = cat["attributes"]
            cat_body_attrs = {}
            for attr in ["name", "description", "capacity", "position"]:
                if cat_attrs.get(attr) is not None:
                    cat_body_attrs[attr] = cat_attrs[attr]
            if cat_body_attrs:
                cat_body = pco.template("EventCategory", cat_body_attrs)
                cat_response = await asyncio.to_thread(
                    pco.post,
                    f"/registrations/v2/events/{new_event_id}/event_categories",
                    cat_body,
                )
                copied_categories.append(cat_response["data"])
    except Exception:
        pass  # Categories may not be supported; continue

    # Copy event times
    try:
        times_response = await asyncio.to_thread(
            pco.get,
            f"/registrations/v2/events/{event_id}/event_times"
        )
        for time in times_response.get("data", []):
            time_attrs = time["attributes"]
            time_body_attrs = {}
            for attr in ["starts_at", "ends_at", "name"]:
                if time_attrs.get(attr) is not None:
                    time_body_attrs[attr] = time_attrs[attr]
            if time_body_attrs:
                time_body = pco.template("EventTime", time_body_attrs)
                time_response = await asyncio.to_thread(
                    pco.post,
                    f"/registrations/v2/events/{new_event_id}/event_times",
                    time_body,
                )
                copied_times.append(time_response["data"])
    except Exception:
        pass  # Event times may not be supported; continue

    return {
        "event": new_event,
        "copied_categories": copied_categories,
        "copied_event_times": copied_times,
        "message": f"Event duplicated successfully as '{copy_name}'.",
    }
