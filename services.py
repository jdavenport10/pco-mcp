import asyncio
import os

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth import OAuthProxy, AccessToken, TokenVerifier
from fastmcp.server.dependencies import Depends
from pypco import PCO

# Load environment variables from .env file
load_dotenv()


# =============================================================================
# OAuth Authentication
# =============================================================================

class PCOTokenVerifier(TokenVerifier):
    """Validates PCO OAuth tokens by calling the PCO API."""

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.planningcenteronline.com/people/v2/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )
                if resp.status_code != 200:
                    return None

                data = resp.json()["data"]
                attrs = data["attributes"]

                return AccessToken(
                    token=token,
                    client_id="pco",
                    scopes=["services", "people"],
                    claims={
                        "sub": data["id"],
                        "name": f"{attrs.get('first_name', '')} {attrs.get('last_name', '')}".strip(),
                        "email": attrs.get("primary_email_address"),
                        "pco_access_token": token,
                    },
                )
        except Exception:
            return None


auth = OAuthProxy(
    upstream_authorization_endpoint="https://api.planningcenteronline.com/oauth/authorize",
    upstream_token_endpoint="https://api.planningcenteronline.com/oauth/token",
    upstream_client_id=os.environ["PCO_CLIENT_ID"],
    upstream_client_secret=os.environ["PCO_CLIENT_SECRET"],
    token_verifier=PCOTokenVerifier(),
    base_url=os.environ.get("BASE_URL", "http://localhost:8000"),
    extra_authorize_params={"scope": "services people registrations"},
    jwt_signing_key=os.environ.get("JWT_SIGNING_KEY"),
)

mcp = FastMCP("PCO Services MCP Server", auth=auth)


# =============================================================================
# Per-User PCO Client
# =============================================================================

async def get_pco(token: AccessToken) -> PCO:
    """Create a per-user PCO client from the authenticated user's upstream token."""
    upstream_token = token.claims.get("pco_access_token")
    if not upstream_token:
        raise ValueError("No PCO access token available")
    return PCO(token=upstream_token)


def _build_patch_body(resource_type: str, **kwargs) -> dict:
    """Build a JSON:API PATCH body with only non-None attributes."""
    attributes = {k: v for k, v in kwargs.items() if v is not None}
    return {
        "data": {
            "type": resource_type,
            "attributes": attributes
        }
    }


# =============================================================================
# Service Type Operations
# =============================================================================

@mcp.tool()
async def get_service_types(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of service types from the Planning Center Online API.
    """
    response = await asyncio.to_thread(pco.get, '/services/v2/service_types')
    return response['data']

@mcp.tool()
async def create_service_type(name: str, frequency: str = None, sequence: int = None, pco: PCO = Depends(get_pco)) -> dict:
    """
    Create a new service type in Planning Center Online.

    Args:
        name (str): The name of the service type (e.g., "Sunday Morning").
        frequency (str, optional): How often this service occurs (e.g., "every 1 week").
        sequence (int, optional): The order in which this service type appears.

    Returns:
        dict: The created service type data.
    """
    attributes = {"name": name}
    if frequency is not None:
        attributes["frequency"] = frequency
    if sequence is not None:
        attributes["sequence"] = sequence

    body = pco.template("ServiceType", attributes)
    response = await asyncio.to_thread(pco.post, "/services/v2/service_types", body)
    return response["data"]

@mcp.tool()
async def update_service_type(service_type_id: str, name: str = None, frequency: str = None, sequence: int = None, pco: PCO = Depends(get_pco)) -> dict:
    """
    Update an existing service type in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type to update.
        name (str, optional): The new name for the service type.
        frequency (str, optional): The new frequency for the service type.
        sequence (int, optional): The new sequence number for the service type.

    Returns:
        dict: The updated service type data.
    """
    body = _build_patch_body("ServiceType", name=name, frequency=frequency, sequence=sequence)
    response = await asyncio.to_thread(pco.patch, f"/services/v2/service_types/{service_type_id}", body)
    return response["data"]

@mcp.tool()
async def delete_service_type(service_type_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a service type from Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/services/v2/service_types/{service_type_id}")
    return {"success": True, "message": f"Service type {service_type_id} deleted successfully."}


# =============================================================================
# Plan Operations
# =============================================================================

@mcp.tool()
async def get_plans(service_type_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of plans for a specific service type.

    Args:
        service_type_id (str): The ID of the service type.
    """
    response = await asyncio.to_thread(pco.get, f'/services/v2/service_types/{service_type_id}/plans?order=-updated_at')
    return response['data']

@mcp.tool()
async def create_plan(service_type_id: str, title: str = None, public: bool = None, series_title: str = None, pco: PCO = Depends(get_pco)) -> dict:
    """
    Create a new plan for a service type in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type to create the plan under.
        title (str, optional): The title of the plan.
        public (bool, optional): Whether the plan is publicly visible.
        series_title (str, optional): The series title for the plan.

    Returns:
        dict: The created plan data.
    """
    attributes = {}
    if title is not None:
        attributes["title"] = title
    if public is not None:
        attributes["public"] = public
    if series_title is not None:
        attributes["series_title"] = series_title

    body = pco.template("Plan", attributes)
    response = await asyncio.to_thread(pco.post, f"/services/v2/service_types/{service_type_id}/plans", body)
    return response["data"]

@mcp.tool()
async def update_plan(service_type_id: str, plan_id: str, title: str = None, public: bool = None, series_title: str = None, pco: PCO = Depends(get_pco)) -> dict:
    """
    Update an existing plan in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type the plan belongs to.
        plan_id (str): The ID of the plan to update.
        title (str, optional): The new title for the plan.
        public (bool, optional): Whether the plan should be publicly visible.
        series_title (str, optional): The new series title for the plan.

    Returns:
        dict: The updated plan data.
    """
    body = _build_patch_body("Plan", title=title, public=public, series_title=series_title)
    response = await asyncio.to_thread(pco.patch, f"/services/v2/service_types/{service_type_id}/plans/{plan_id}", body)
    return response["data"]

@mcp.tool()
async def delete_plan(service_type_id: str, plan_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a plan from Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type the plan belongs to.
        plan_id (str): The ID of the plan to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/services/v2/service_types/{service_type_id}/plans/{plan_id}")
    return {"success": True, "message": f"Plan {plan_id} deleted successfully."}


# =============================================================================
# Plan Time Operations
# =============================================================================

@mcp.tool()
async def get_plan_times(service_type_id: str, plan_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of times for a specific plan in Planning Center Online.

    Plan times represent scheduled times for a plan such as rehearsals or services.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.

    Returns:
        list: A list of plan time data.
    """
    response = await asyncio.to_thread(pco.get, f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/plan_times")
    return response["data"]

@mcp.tool()
async def create_plan_time(service_type_id: str, plan_id: str, starts_at: str, ends_at: str, time_type: str = None, name: str = None, pco: PCO = Depends(get_pco)) -> dict:
    """
    Create a new plan time for a plan in Planning Center Online.

    Plan times represent scheduled times for a plan such as rehearsals or services.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        starts_at (str): The start time in ISO 8601 format (e.g., "2025-03-01T09:00:00Z").
        ends_at (str): The end time in ISO 8601 format (e.g., "2025-03-01T11:00:00Z").
        time_type (str, optional): The type of time - "rehearsal", "service", or "other".
        name (str, optional): A name for this time (e.g., "Morning Rehearsal").

    Returns:
        dict: The created plan time data.
    """
    attributes = {"starts_at": starts_at, "ends_at": ends_at}
    if time_type is not None:
        attributes["time_type"] = time_type
    if name is not None:
        attributes["name"] = name

    body = pco.template("PlanTime", attributes)
    response = await asyncio.to_thread(
        pco.post,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/plan_times",
        body
    )
    return response["data"]

@mcp.tool()
async def update_plan_time(service_type_id: str, plan_id: str, plan_time_id: str, starts_at: str = None, ends_at: str = None, time_type: str = None, name: str = None, pco: PCO = Depends(get_pco)) -> dict:
    """
    Update an existing plan time in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        plan_time_id (str): The ID of the plan time to update.
        starts_at (str, optional): The new start time in ISO 8601 format.
        ends_at (str, optional): The new end time in ISO 8601 format.
        time_type (str, optional): The new type of time - "rehearsal", "service", or "other".
        name (str, optional): The new name for this time.

    Returns:
        dict: The updated plan time data.
    """
    body = _build_patch_body("PlanTime", starts_at=starts_at, ends_at=ends_at, time_type=time_type, name=name)
    response = await asyncio.to_thread(
        pco.patch,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/plan_times/{plan_time_id}",
        body
    )
    return response["data"]

@mcp.tool()
async def delete_plan_time(service_type_id: str, plan_id: str, plan_time_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a plan time from a plan in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        plan_time_id (str): The ID of the plan time to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(
        pco.delete,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/plan_times/{plan_time_id}"
    )
    return {"success": True, "message": f"Plan time {plan_time_id} deleted successfully."}


# =============================================================================
# Plan Item Operations
# =============================================================================

@mcp.tool()
async def get_plan_items(plan_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of items for a specific plan.

    Args:
        plan_id (str): The ID of the plan.
    """
    response = await asyncio.to_thread(pco.get, f'/services/v2/plans/{plan_id}/items')
    return response['data']

@mcp.tool()
async def create_plan_item(
    service_type_id: str,
    plan_id: str,
    title: str,
    item_type: str,
    length: int = None,
    service_position: str = None,
    description: str = None,
    song_id: str = None,
    arrangement_id: str = None,
    key_id: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new item in a plan in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        title (str): The title of the item.
        item_type (str): The type of item - "song", "header", "media", or "item".
        length (int, optional): The length of the item in seconds.
        service_position (str, optional): Position in service - "pre" or "post" (omit for during).
        description (str, optional): A description for the item.
        song_id (str, optional): The ID of a song to associate (for song items).
        arrangement_id (str, optional): The ID of a specific arrangement to use.
        key_id (str, optional): The ID of a specific key to use.

    Returns:
        dict: The created item data.
    """
    attributes = {"title": title, "item_type": item_type}
    if length is not None:
        attributes["length"] = length
    if service_position is not None:
        attributes["service_position"] = service_position
    if description is not None:
        attributes["description"] = description
    if song_id is not None:
        attributes["song_id"] = song_id
    if arrangement_id is not None:
        attributes["arrangement_id"] = arrangement_id
    if key_id is not None:
        attributes["key_id"] = key_id

    body = pco.template("Item", attributes)
    response = await asyncio.to_thread(
        pco.post,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/items",
        body
    )
    return response["data"]

@mcp.tool()
async def update_plan_item(
    service_type_id: str,
    plan_id: str,
    item_id: str,
    title: str = None,
    length: int = None,
    service_position: str = None,
    description: str = None,
    sequence: int = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing item in a plan in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        item_id (str): The ID of the item to update.
        title (str, optional): The new title for the item.
        length (int, optional): The new length in seconds.
        service_position (str, optional): New position - "pre" or "post" (omit for during).
        description (str, optional): The new description.
        sequence (int, optional): The new sequence number for ordering.

    Returns:
        dict: The updated item data.
    """
    body = _build_patch_body(
        "Item",
        title=title,
        length=length,
        service_position=service_position,
        description=description,
        sequence=sequence
    )
    response = await asyncio.to_thread(
        pco.patch,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/items/{item_id}",
        body
    )
    return response["data"]

@mcp.tool()
async def delete_plan_item(service_type_id: str, plan_id: str, item_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete an item from a plan in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        item_id (str): The ID of the item to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(
        pco.delete,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/items/{item_id}"
    )
    return {"success": True, "message": f"Plan item {item_id} deleted successfully."}

@mcp.tool()
async def reorder_plan_items(service_type_id: str, plan_id: str, item_ids: list[str], pco: PCO = Depends(get_pco)) -> dict:
    """
    Reorder items within a plan in Planning Center Online.

    The items will be arranged in the order specified by the item_ids list.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        item_ids (list[str]): An ordered list of item IDs representing the desired order.

    Returns:
        dict: A confirmation message.
    """
    body = {
        "data": {
            "type": "ItemReorder",
            "attributes": {
                "sequence": item_ids
            }
        }
    }
    await asyncio.to_thread(
        pco.post,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/item_reorder",
        body
    )
    return {"success": True, "message": "Plan items reordered successfully."}


# =============================================================================
# Team Member Operations
# =============================================================================

@mcp.tool()
async def get_plan_team_members(plan_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of team members for a specific plan.

    Args:
        plan_id (str): The ID of the plan.
    """
    response = await asyncio.to_thread(pco.get, f'/services/v2/plans/{plan_id}/team_members')
    return response['data']

@mcp.tool()
async def assign_team_member(
    service_type_id: str,
    plan_id: str,
    person_id: str,
    team_position_name: str = None,
    status: str = None,
    prepare_notification: bool = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Assign a person as a team member to a plan in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        person_id (str): The ID of the person to assign.
        team_position_name (str, optional): The team position name (e.g., "Vocals", "Sound").
        status (str, optional): The status - "C" (confirmed), "U" (unconfirmed), or "D" (declined).
        prepare_notification (bool, optional): Whether to send a notification to the person.

    Returns:
        dict: The created team member assignment data.
    """
    attributes = {}
    if team_position_name is not None:
        attributes["team_position_name"] = team_position_name
    if status is not None:
        attributes["status"] = status
    if prepare_notification is not None:
        attributes["prepare_notification"] = prepare_notification

    body = {
        "data": {
            "type": "PlanPerson",
            "attributes": attributes,
            "relationships": {
                "person": {
                    "data": {"type": "Person", "id": person_id}
                }
            }
        }
    }

    response = await asyncio.to_thread(
        pco.post,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/team_members",
        body
    )
    return response["data"]

@mcp.tool()
async def update_team_member(
    service_type_id: str,
    plan_id: str,
    team_member_id: str,
    status: str = None,
    notes: str = None,
    team_position_name: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing team member assignment on a plan in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        team_member_id (str): The ID of the team member assignment to update.
        status (str, optional): The new status - "C" (confirmed), "U" (unconfirmed), or "D" (declined).
        notes (str, optional): Notes for the team member.
        team_position_name (str, optional): The new team position name.

    Returns:
        dict: The updated team member data.
    """
    body = _build_patch_body(
        "PlanPerson",
        status=status,
        notes=notes,
        team_position_name=team_position_name
    )
    response = await asyncio.to_thread(
        pco.patch,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/team_members/{team_member_id}",
        body
    )
    return response["data"]

@mcp.tool()
async def remove_team_member(service_type_id: str, plan_id: str, team_member_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Remove a team member from a plan in Planning Center Online.

    Args:
        service_type_id (str): The ID of the service type.
        plan_id (str): The ID of the plan.
        team_member_id (str): The ID of the team member assignment to remove.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(
        pco.delete,
        f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/team_members/{team_member_id}"
    )
    return {"success": True, "message": f"Team member {team_member_id} removed successfully."}


# =============================================================================
# Schedule Operations
# =============================================================================

@mcp.tool()
async def get_person_schedules(person_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of schedules for a specific person in Planning Center Online.

    Schedules represent a person's upcoming service assignments.

    Args:
        person_id (str): The ID of the person.

    Returns:
        list: A list of schedule data for the person.
    """
    response = await asyncio.to_thread(pco.get, f"/services/v2/people/{person_id}/schedules")
    return response["data"]

@mcp.tool()
async def accept_schedule(person_id: str, schedule_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Accept a schedule assignment for a person in Planning Center Online.

    Args:
        person_id (str): The ID of the person.
        schedule_id (str): The ID of the schedule to accept.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(
        pco.post,
        f"/services/v2/people/{person_id}/schedules/{schedule_id}/accept",
        {}
    )
    return {"success": True, "message": f"Schedule {schedule_id} accepted successfully."}

@mcp.tool()
async def decline_schedule(person_id: str, schedule_id: str, reason: str = None, pco: PCO = Depends(get_pco)) -> dict:
    """
    Decline a schedule assignment for a person in Planning Center Online.

    Args:
        person_id (str): The ID of the person.
        schedule_id (str): The ID of the schedule to decline.
        reason (str, optional): The reason for declining the schedule.

    Returns:
        dict: A confirmation message.
    """
    body = {}
    if reason is not None:
        body = {"data": {"attributes": {"reason": reason}}}

    await asyncio.to_thread(
        pco.post,
        f"/services/v2/people/{person_id}/schedules/{schedule_id}/decline",
        body
    )
    return {"success": True, "message": f"Schedule {schedule_id} declined successfully."}


# =============================================================================
# Song Operations
# =============================================================================

@mcp.tool()
async def get_songs(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of songs from the Planning Center Online API.
    """
    response = await asyncio.to_thread(pco.get, '/services/v2/songs?per_page=200&where[hidden]=false')
    return response['data']

@mcp.tool()
async def get_song(song_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific song.

    Args:
        song_id (str): The ID of the song.
    """
    response = await asyncio.to_thread(pco.get, f'/services/v2/songs/{song_id}')
    return response['data']

@mcp.tool()
async def find_song_by_title(title: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Find songs by title.

    Args:
        title (str): The title of the song to search for.

    Returns:
        list: List of songs matching the title.
    """
    response = await asyncio.to_thread(pco.get, f'/services/v2/songs?where[title]={title}&where[hidden]=false')
    return response['data']

@mcp.tool()
async def create_song(title: str, ccli: str = None, pco: PCO = Depends(get_pco)) -> dict:
    """
    Create a new song in Planning Center Online.

    Args:
        title (str): The title of the song.
        ccli (str, optional): The CCLI number for the song.

    Returns:
        dict: The created song data.
    """
    attributes = {"title": title}
    if ccli:
        attributes["ccli_number"] = ccli

    body = pco.template('Song', attributes)
    response = await asyncio.to_thread(pco.post, '/services/v2/songs', body)
    return response['data']

@mcp.tool()
async def get_all_arrangements_for_song(song_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Get a list of all the arrangements for a particular song from the Planning Center Online API.

    Args:
        song_id (str): The ID for the song.
    """
    response = await asyncio.to_thread(pco.get, f'/services/v2/songs/{song_id}/arrangements')
    return response['data']

@mcp.tool()
async def get_arrangement_for_song(song_id: str, arrangement_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Get information for a particular song from the Planning Center Online API.

    Args:
        song_id (str): The ID for the song.
        arrangement_id (str): The ID for the arrangement within a song.
    """
    response = await asyncio.to_thread(pco.get, f'/services/v2/songs/{song_id}/arrangements/{arrangement_id}')
    return response['data']

@mcp.tool()
async def get_keys_for_arrangement_of_song(song_id: str, arrangement_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Get a list of keys available for a particular song ID and arrangement ID from the Planning Center Online API.

    Args:
        song_id (str): The ID for the song.
        arrangement_id (str): The ID for the arrangement within a song.
    """
    response = await asyncio.to_thread(pco.get, f'/services/v2/songs/{song_id}/arrangements/{arrangement_id}/keys')
    return response['data']


# =============================================================================
# Tag Operations
# =============================================================================

@mcp.tool()
async def assign_tags_to_song(song_id: str, tag_names: list[str], pco: PCO = Depends(get_pco)) -> dict:
    """
    Assign tags to a specific song.

    Args:
        song_id (str): The ID of the song.
        tag_names (list[str]): List of tag names to assign to the song.

    Returns:
        dict: Success status and message.
    """
    tag_groups_response = await asyncio.to_thread(pco.get, '/services/v2/tag_groups?include=tags&filter=song')

    included_tags = tag_groups_response.get('included', [])

    tag_data = []
    for tag_name in tag_names:
        for tag in included_tags:
            if tag['type'] == 'Tag' and tag['attributes']['name'].lower() == tag_name.lower():
                tag_data.append({
                    "type": "Tag",
                    "id": tag['id']
                })
                break

    if not tag_data:
        return {"success": False, "message": "No matching tags found"}

    body = {
        "data": {
            "type": "TagAssignment",
            "attributes": {},
            "relationships": {
                "tags": {
                    "data": tag_data
                }
            }
        }
    }

    await asyncio.to_thread(pco.post, f'/services/v2/songs/{song_id}/assign_tags', body)

    return {"success": True, "message": f"Successfully assigned {len(tag_data)} tag(s) to song {song_id}"}

@mcp.tool()
async def find_songs_by_tags(tag_names: list[str], pco: PCO = Depends(get_pco)) -> list:
    """
    Find songs that have all of the specified tags.

    Args:
        tag_names (list[str]): List of tag names to filter songs by. Songs must have all specified tags.
    """
    tag_groups_response = await asyncio.to_thread(pco.get, '/services/v2/tag_groups?include=tags&filter=song')

    included_tags = tag_groups_response.get('included', [])

    tag_ids = []
    for tag_name in tag_names:
        for tag in included_tags:
            if tag['type'] == 'Tag' and tag['attributes']['name'].lower() == tag_name.lower():
                tag_ids.append(tag['id'])
                break

    if not tag_ids:
        return []

    tag_filters = '&'.join([f'where[song_tag_ids]={tag_id}' for tag_id in tag_ids])
    query = f'/services/v2/songs?per_page=200&where[hidden]=false&{tag_filters}'

    response = await asyncio.to_thread(pco.get, query)
    return response['data']


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


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
