import asyncio

from fastmcp.server.dependencies import Depends
from pypco import PCO

from server import mcp, get_pco, _build_patch_body


# =============================================================================
# Calendar Event Operations
# =============================================================================

@mcp.tool()
async def get_calendar_events(filter: str = "future", pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of calendar events from Planning Center Online.

    Args:
        filter (str, optional): Filter for events. Common values: "future", "past",
            "approved", "pending". Defaults to "future".

    Returns:
        list: A list of calendar event data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/calendar/v2/events?filter={filter}&order=starts_at"
    )
    return response["data"]

@mcp.tool()
async def get_calendar_event(event_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific calendar event.

    Args:
        event_id (str): The ID of the calendar event.

    Returns:
        dict: The calendar event data.
    """
    response = await asyncio.to_thread(pco.get, f"/calendar/v2/events/{event_id}")
    return response["data"]

@mcp.tool()
async def create_calendar_event(
    name: str,
    description: str = None,
    starts_at: str = None,
    ends_at: str = None,
    approval_status: str = None,
    visible_in_church_center: bool = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new calendar event in Planning Center Online.

    Args:
        name (str): The name of the event.
        description (str, optional): A description of the event.
        starts_at (str, optional): The start time in ISO 8601 format.
        ends_at (str, optional): The end time in ISO 8601 format.
        approval_status (str, optional): The approval status (e.g., "approved", "pending").
        visible_in_church_center (bool, optional): Whether the event is visible in Church Center.

    Returns:
        dict: The created calendar event data.
    """
    attributes = {"name": name}
    if description is not None:
        attributes["description"] = description
    if starts_at is not None:
        attributes["starts_at"] = starts_at
    if ends_at is not None:
        attributes["ends_at"] = ends_at
    if approval_status is not None:
        attributes["approval_status"] = approval_status
    if visible_in_church_center is not None:
        attributes["visible_in_church_center"] = visible_in_church_center

    body = pco.template("Event", attributes)
    response = await asyncio.to_thread(pco.post, "/calendar/v2/events", body)
    return response["data"]

@mcp.tool()
async def update_calendar_event(
    event_id: str,
    name: str = None,
    description: str = None,
    starts_at: str = None,
    ends_at: str = None,
    approval_status: str = None,
    visible_in_church_center: bool = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing calendar event in Planning Center Online.

    Args:
        event_id (str): The ID of the event to update.
        name (str, optional): The new name for the event.
        description (str, optional): The new description.
        starts_at (str, optional): The new start time in ISO 8601 format.
        ends_at (str, optional): The new end time in ISO 8601 format.
        approval_status (str, optional): The new approval status.
        visible_in_church_center (bool, optional): Whether visible in Church Center.

    Returns:
        dict: The updated calendar event data.
    """
    body = _build_patch_body(
        "Event",
        name=name,
        description=description,
        starts_at=starts_at,
        ends_at=ends_at,
        approval_status=approval_status,
        visible_in_church_center=visible_in_church_center,
    )
    response = await asyncio.to_thread(pco.patch, f"/calendar/v2/events/{event_id}", body)
    return response["data"]

@mcp.tool()
async def delete_calendar_event(event_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a calendar event from Planning Center Online.

    Args:
        event_id (str): The ID of the event to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/calendar/v2/events/{event_id}")
    return {"success": True, "message": f"Calendar event {event_id} deleted successfully."}


# =============================================================================
# Event Instance Operations
# =============================================================================

@mcp.tool()
async def get_event_instances(event_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch instances of a calendar event.

    Event instances represent individual occurrences of an event,
    especially useful for recurring events.

    Args:
        event_id (str): The ID of the calendar event.

    Returns:
        list: A list of event instance data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/calendar/v2/events/{event_id}/event_instances"
    )
    return response["data"]

@mcp.tool()
async def get_event_instance(event_instance_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific event instance.

    Args:
        event_instance_id (str): The ID of the event instance.

    Returns:
        dict: The event instance data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/calendar/v2/event_instances/{event_instance_id}"
    )
    return response["data"]

@mcp.tool()
async def get_upcoming_event_instances(filter: str = "future", pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch upcoming event instances across all calendar events.

    Args:
        filter (str, optional): Filter for instances. Common values: "future", "past",
            "approved". Defaults to "future".

    Returns:
        list: A list of upcoming event instance data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/calendar/v2/event_instances?filter={filter}&order=starts_at"
    )
    return response["data"]


# =============================================================================
# Event Resource Booking Operations
# =============================================================================

@mcp.tool()
async def get_calendar_resources(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of resources (rooms, equipment, etc.) from Planning Center Calendar.

    Returns:
        list: A list of resource data.
    """
    response = await asyncio.to_thread(pco.get, "/calendar/v2/resources")
    return response["data"]

@mcp.tool()
async def get_calendar_resource(resource_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific calendar resource.

    Args:
        resource_id (str): The ID of the resource.

    Returns:
        dict: The resource data.
    """
    response = await asyncio.to_thread(pco.get, f"/calendar/v2/resources/{resource_id}")
    return response["data"]

@mcp.tool()
async def create_calendar_resource(
    name: str,
    kind: str = None,
    description: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new resource in Planning Center Calendar.

    Args:
        name (str): The name of the resource (e.g., "Main Sanctuary", "Projector").
        kind (str, optional): The kind of resource (e.g., "Room", "Resource").
        description (str, optional): A description of the resource.

    Returns:
        dict: The created resource data.
    """
    attributes = {"name": name}
    if kind is not None:
        attributes["kind"] = kind
    if description is not None:
        attributes["description"] = description

    body = pco.template("Resource", attributes)
    response = await asyncio.to_thread(pco.post, "/calendar/v2/resources", body)
    return response["data"]

@mcp.tool()
async def update_calendar_resource(
    resource_id: str,
    name: str = None,
    kind: str = None,
    description: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing resource in Planning Center Calendar.

    Args:
        resource_id (str): The ID of the resource to update.
        name (str, optional): The new name.
        kind (str, optional): The new kind.
        description (str, optional): The new description.

    Returns:
        dict: The updated resource data.
    """
    body = _build_patch_body("Resource", name=name, kind=kind, description=description)
    response = await asyncio.to_thread(pco.patch, f"/calendar/v2/resources/{resource_id}", body)
    return response["data"]

@mcp.tool()
async def delete_calendar_resource(resource_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a resource from Planning Center Calendar.

    Args:
        resource_id (str): The ID of the resource to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/calendar/v2/resources/{resource_id}")
    return {"success": True, "message": f"Resource {resource_id} deleted successfully."}

@mcp.tool()
async def get_event_resource_requests(event_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch resource requests (bookings) for a specific calendar event.

    Args:
        event_id (str): The ID of the calendar event.

    Returns:
        list: A list of resource request data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/calendar/v2/events/{event_id}/resource_bookings"
    )
    return response["data"]


# =============================================================================
# Calendar Tag Operations
# =============================================================================

@mcp.tool()
async def get_calendar_tag_groups(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch tag groups from Planning Center Calendar.

    Tag groups organize tags by category (e.g., departments, ministries, campuses).

    Returns:
        list: A list of tag group data.
    """
    response = await asyncio.to_thread(pco.get, "/calendar/v2/tag_groups?include=tags")
    return response["data"]

@mcp.tool()
async def get_calendar_event_tags(event_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch tags assigned to a specific calendar event.

    Args:
        event_id (str): The ID of the calendar event.

    Returns:
        list: A list of tag data for this event.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/calendar/v2/events/{event_id}/tags"
    )
    return response["data"]


# =============================================================================
# Calendar Feed Operations
# =============================================================================

@mcp.tool()
async def get_calendar_feeds(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of calendar feeds from Planning Center Calendar.

    Feeds are used to share calendar data with external calendar applications.

    Returns:
        list: A list of feed data.
    """
    response = await asyncio.to_thread(pco.get, "/calendar/v2/feeds")
    return response["data"]

@mcp.tool()
async def get_calendar_feed(feed_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific calendar feed.

    Args:
        feed_id (str): The ID of the feed.

    Returns:
        dict: The feed data.
    """
    response = await asyncio.to_thread(pco.get, f"/calendar/v2/feeds/{feed_id}")
    return response["data"]


# =============================================================================
# Conflict Operations
# =============================================================================

@mcp.tool()
async def get_calendar_conflicts(resource_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch booking conflicts for a specific resource.

    Args:
        resource_id (str): The ID of the resource to check for conflicts.

    Returns:
        list: A list of conflict data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/calendar/v2/resources/{resource_id}/conflicts"
    )
    return response["data"]
