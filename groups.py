import asyncio

from fastmcp.dependencies import Depends
from pypco import PCO

from app import mcp, get_pco, _build_patch_body


# =============================================================================
# Group Operations
# =============================================================================

@mcp.tool()
async def get_groups(
    name: str = None,
    archive_status: str = None,
    group_type_id: str = None,
    per_page: int = 25,
    pco: PCO = Depends(get_pco),
) -> list:
    """
    Fetch a list of groups from Planning Center Groups.

    Args:
        name (str, optional): Filter by group name.
        archive_status (str, optional): Filter by archive status - "not_archived", "only", or "include".
        group_type_id (str, optional): Filter by group type ID.
        per_page (int, optional): Number of results per page (max 100). Default: 25.

    Returns:
        list: A list of group data.
    """
    params = [f"per_page={min(per_page, 100)}", "order=name"]

    if name:
        params.append(f"where[name]={name}")
    if archive_status:
        params.append(f"where[archive_status]={archive_status}")
    if group_type_id:
        params.append(f"filter=group_type&group_type_id={group_type_id}")

    path = "/groups/v2/groups?" + "&".join(params)
    response = await asyncio.to_thread(pco.get, path)
    return response["data"]


@mcp.tool()
async def get_group(group_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific group.

    Args:
        group_id (str): The ID of the group.

    Returns:
        dict: The group data with included group type, location, and enrollment.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/groups/v2/groups/{group_id}?include=group_type,location,enrollment",
    )
    return response


@mcp.tool()
async def update_group(
    group_id: str,
    name: str = None,
    schedule: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing group in Planning Center Groups.

    Args:
        group_id (str): The ID of the group to update.
        name (str, optional): The new name for the group.
        schedule (str, optional): A text summary of the group's meeting schedule (e.g., "Sundays at 9:30am").

    Returns:
        dict: The updated group data.
    """
    body = _build_patch_body("Group", name=name, schedule=schedule)
    response = await asyncio.to_thread(pco.patch, f"/groups/v2/groups/{group_id}", body)
    return response["data"]


@mcp.tool()
async def get_group_people(group_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch people who are members of a specific group.

    Args:
        group_id (str): The ID of the group.

    Returns:
        list: A list of person data for group members.
    """
    response = await asyncio.to_thread(
        pco.get, f"/groups/v2/groups/{group_id}/people?per_page=100"
    )
    return response["data"]


# =============================================================================
# GroupType Operations
# =============================================================================

@mcp.tool()
async def get_group_types(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of group types from Planning Center Groups.

    Group types are categories of groups (e.g., "Small Groups", "Classes").

    Returns:
        list: A list of group type data.
    """
    response = await asyncio.to_thread(
        pco.get, "/groups/v2/group_types?per_page=100&order=position"
    )
    return response["data"]


@mcp.tool()
async def get_group_type(group_type_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific group type.

    Args:
        group_type_id (str): The ID of the group type.

    Returns:
        dict: The group type data.
    """
    response = await asyncio.to_thread(pco.get, f"/groups/v2/group_types/{group_type_id}")
    return response["data"]


# =============================================================================
# Membership Operations
# =============================================================================

@mcp.tool()
async def get_group_memberships(
    group_id: str,
    role: str = None,
    pco: PCO = Depends(get_pco),
) -> list:
    """
    Fetch a list of memberships for a specific group.

    Args:
        group_id (str): The ID of the group.
        role (str, optional): Filter by role - "member" or "leader".

    Returns:
        list: A list of membership data.
    """
    params = ["per_page=100", "include=person", "order=last_name"]
    if role:
        params.append(f"where[role]={role}")

    path = f"/groups/v2/groups/{group_id}/memberships?" + "&".join(params)
    response = await asyncio.to_thread(pco.get, path)
    return response["data"]


@mcp.tool()
async def get_person_memberships(person_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch all group memberships for a specific person.

    Args:
        person_id (str): The ID of the person.

    Returns:
        list: A list of membership data for this person.
    """
    response = await asyncio.to_thread(
        pco.get, f"/groups/v2/people/{person_id}/memberships?include=group"
    )
    return response["data"]


@mcp.tool()
async def create_group_membership(
    group_id: str,
    person_id: str,
    role: str = "member",
    joined_at: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Add a person as a member of a group in Planning Center Groups.

    Args:
        group_id (str): The ID of the group.
        person_id (str): The ID of the person to add.
        role (str, optional): The role - "member" or "leader". Default: "member".
        joined_at (str, optional): The join date in ISO 8601 format (e.g., "2025-01-01T00:00:00Z").

    Returns:
        dict: The created membership data.
    """
    attributes: dict = {"role": role}
    if joined_at is not None:
        attributes["joined_at"] = joined_at

    body = {
        "data": {
            "type": "Membership",
            "attributes": attributes,
            "relationships": {
                "person": {"data": {"type": "Person", "id": person_id}}
            },
        }
    }
    response = await asyncio.to_thread(
        pco.post, f"/groups/v2/groups/{group_id}/memberships", body
    )
    return response["data"]


@mcp.tool()
async def update_group_membership(
    group_id: str,
    membership_id: str,
    role: str = None,
    joined_at: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing group membership in Planning Center Groups.

    Args:
        group_id (str): The ID of the group.
        membership_id (str): The ID of the membership to update.
        role (str, optional): The new role - "member" or "leader".
        joined_at (str, optional): The new join date in ISO 8601 format.

    Returns:
        dict: The updated membership data.
    """
    body = _build_patch_body("Membership", role=role, joined_at=joined_at)
    response = await asyncio.to_thread(
        pco.patch, f"/groups/v2/groups/{group_id}/memberships/{membership_id}", body
    )
    return response["data"]


@mcp.tool()
async def delete_group_membership(
    group_id: str,
    membership_id: str,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Remove a person from a group in Planning Center Groups.

    Args:
        group_id (str): The ID of the group.
        membership_id (str): The ID of the membership to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(
        pco.delete, f"/groups/v2/groups/{group_id}/memberships/{membership_id}"
    )
    return {"success": True, "message": f"Membership {membership_id} deleted successfully."}


# =============================================================================
# Event Operations
# =============================================================================

@mcp.tool()
async def get_events(
    filter: str = None,
    group_type_id: str = None,
    per_page: int = 25,
    pco: PCO = Depends(get_pco),
) -> list:
    """
    Fetch a list of events across all groups from Planning Center Groups.

    Args:
        filter (str, optional): Filter events - "upcoming", "canceled", or "not_canceled".
        group_type_id (str, optional): Filter events by group type ID.
        per_page (int, optional): Number of results per page (max 100). Default: 25.

    Returns:
        list: A list of event data.
    """
    params = [f"per_page={min(per_page, 100)}", "order=starts_at"]

    if filter:
        params.append(f"filter={filter}")
    if group_type_id:
        params.append(f"filter=group_type&group_type_id={group_type_id}")

    path = "/groups/v2/events?" + "&".join(params)
    response = await asyncio.to_thread(pco.get, path)
    return response["data"]


@mcp.tool()
async def get_group_events(
    group_id: str,
    filter: str = None,
    pco: PCO = Depends(get_pco),
) -> list:
    """
    Fetch a list of events for a specific group.

    Args:
        group_id (str): The ID of the group.
        filter (str, optional): Filter events - "canceled" or "not_canceled".

    Returns:
        list: A list of event data for this group.
    """
    params = ["per_page=100", "order=starts_at", "include=location"]
    if filter:
        params.append(f"filter={filter}")

    path = f"/groups/v2/groups/{group_id}/events?" + "&".join(params)
    response = await asyncio.to_thread(pco.get, path)
    return response["data"]


@mcp.tool()
async def get_event(event_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific group event.

    Args:
        event_id (str): The ID of the event.

    Returns:
        dict: The event data with included group and location.
    """
    response = await asyncio.to_thread(
        pco.get, f"/groups/v2/events/{event_id}?include=group,location"
    )
    return response


# =============================================================================
# Attendance Operations
# =============================================================================

@mcp.tool()
async def get_event_attendances(
    event_id: str,
    role: str = None,
    attended_only: bool = False,
    pco: PCO = Depends(get_pco),
) -> list:
    """
    Fetch attendance records for a specific group event.

    Args:
        event_id (str): The ID of the event.
        role (str, optional): Filter by role - "member", "leader", "visitor", or "applicant".
        attended_only (bool, optional): If True, only return attendees who attended. Default: False.

    Returns:
        list: A list of attendance data including person info.
    """
    params = ["per_page=100", "include=person", "order=last_name"]

    if role:
        params.append(f"where[role]={role}")
    if attended_only:
        params.append("filter=attended")

    path = f"/groups/v2/events/{event_id}/attendances?" + "&".join(params)
    response = await asyncio.to_thread(pco.get, path)
    return response["data"]
