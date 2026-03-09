import asyncio
from typing import Optional

from fastmcp.dependencies import Depends
from pypco import PCO

from app import mcp, get_pco, _build_patch_body


# =============================================================================
# Person Operations
# =============================================================================

@mcp.tool()
async def get_people(
    search: str = None,
    first_name: str = None,
    last_name: str = None,
    status: str = None,
    child: bool = None,
    per_page: int = 25,
    pco: PCO = Depends(get_pco),
) -> list:
    """
    Fetch a list of people from Planning Center People.

    Args:
        search (str, optional): Search by name, email, or phone number.
        first_name (str, optional): Filter by exact first name.
        last_name (str, optional): Filter by exact last name.
        status (str, optional): Filter by status - "active" or "inactive".
        child (bool, optional): Filter by child flag.
        per_page (int, optional): Number of results per page (max 100). Default: 25.

    Returns:
        list: A list of person data.
    """
    params = [f"per_page={min(per_page, 100)}", "order=last_name"]

    if search:
        params.append(f"where[search_name_or_email_or_phone_number]={search}")
    if first_name:
        params.append(f"where[first_name]={first_name}")
    if last_name:
        params.append(f"where[last_name]={last_name}")
    if status:
        params.append(f"where[status]={status}")
    if child is not None:
        params.append(f"where[child]={'true' if child else 'false'}")

    path = "/people/v2/people?" + "&".join(params)
    response = await asyncio.to_thread(pco.get, path)
    return response["data"]


@mcp.tool()
async def get_person(person_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific person, including their emails, phone numbers,
    addresses, and household memberships.

    Args:
        person_id (str): The ID of the person.

    Returns:
        dict: The person data with included contact details.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/people/v2/people/{person_id}?include=emails,phone_numbers,addresses,households",
    )
    return response


@mcp.tool()
async def get_me(pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch the profile of the currently authenticated user.

    Returns:
        dict: The current user's person data.
    """
    response = await asyncio.to_thread(pco.get, "/people/v2/me")
    return response["data"]


@mcp.tool()
async def create_person(
    first_name: str,
    last_name: str,
    gender: str = None,
    birthdate: str = None,
    anniversary: str = None,
    membership: str = None,
    status: str = None,
    child: bool = None,
    grade: int = None,
    graduation_year: int = None,
    medical_notes: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new person in Planning Center People.

    Args:
        first_name (str): The person's first name.
        last_name (str): The person's last name.
        gender (str, optional): Gender - "M" or "F".
        birthdate (str, optional): Birthdate in YYYY-MM-DD format.
        anniversary (str, optional): Anniversary in YYYY-MM-DD format.
        membership (str, optional): Membership type (e.g., "Member", "Regular Attender").
        status (str, optional): Status - "active" or "inactive".
        child (bool, optional): Whether this person is a child.
        grade (int, optional): School grade.
        graduation_year (int, optional): Graduation year.
        medical_notes (str, optional): Medical notes for the person.

    Returns:
        dict: The created person data.
    """
    attributes = {"first_name": first_name, "last_name": last_name}
    if gender is not None:
        attributes["gender"] = gender
    if birthdate is not None:
        attributes["birthdate"] = birthdate
    if anniversary is not None:
        attributes["anniversary"] = anniversary
    if membership is not None:
        attributes["membership"] = membership
    if status is not None:
        attributes["status"] = status
    if child is not None:
        attributes["child"] = child
    if grade is not None:
        attributes["grade"] = grade
    if graduation_year is not None:
        attributes["graduation_year"] = graduation_year
    if medical_notes is not None:
        attributes["medical_notes"] = medical_notes

    body = pco.template("Person", attributes)
    response = await asyncio.to_thread(pco.post, "/people/v2/people", body)
    return response["data"]


@mcp.tool()
async def update_person(
    person_id: str,
    first_name: str = None,
    last_name: str = None,
    gender: str = None,
    birthdate: str = None,
    anniversary: str = None,
    membership: str = None,
    status: str = None,
    child: bool = None,
    grade: int = None,
    graduation_year: int = None,
    medical_notes: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing person in Planning Center People.

    Args:
        person_id (str): The ID of the person to update.
        first_name (str, optional): The new first name.
        last_name (str, optional): The new last name.
        gender (str, optional): Gender - "M" or "F".
        birthdate (str, optional): Birthdate in YYYY-MM-DD format.
        anniversary (str, optional): Anniversary in YYYY-MM-DD format.
        membership (str, optional): Membership type.
        status (str, optional): Status - "active" or "inactive".
        child (bool, optional): Whether this person is a child.
        grade (int, optional): School grade.
        graduation_year (int, optional): Graduation year.
        medical_notes (str, optional): Medical notes.

    Returns:
        dict: The updated person data.
    """
    body = _build_patch_body(
        "Person",
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        birthdate=birthdate,
        anniversary=anniversary,
        membership=membership,
        status=status,
        child=child,
        grade=grade,
        graduation_year=graduation_year,
        medical_notes=medical_notes,
    )
    response = await asyncio.to_thread(pco.patch, f"/people/v2/people/{person_id}", body)
    return response["data"]


@mcp.tool()
async def delete_person(person_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a person from Planning Center People.

    Args:
        person_id (str): The ID of the person to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/people/v2/people/{person_id}")
    return {"success": True, "message": f"Person {person_id} deleted successfully."}


# =============================================================================
# Email Operations
# =============================================================================

@mcp.tool()
async def get_person_emails(person_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of email addresses for a specific person.

    Args:
        person_id (str): The ID of the person.

    Returns:
        list: A list of email data.
    """
    response = await asyncio.to_thread(pco.get, f"/people/v2/people/{person_id}/emails")
    return response["data"]


@mcp.tool()
async def create_person_email(
    person_id: str,
    address: str,
    location: str = "Home",
    primary: bool = False,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Add an email address to a person in Planning Center People.

    Args:
        person_id (str): The ID of the person.
        address (str): The email address.
        location (str, optional): Location label (e.g., "Home", "Work"). Default: "Home".
        primary (bool, optional): Whether this is the primary email. Default: False.

    Returns:
        dict: The created email data.
    """
    body = pco.template("Email", {"address": address, "location": location, "primary": primary})
    response = await asyncio.to_thread(pco.post, f"/people/v2/people/{person_id}/emails", body)
    return response["data"]


@mcp.tool()
async def update_email(
    email_id: str,
    address: str = None,
    location: str = None,
    primary: bool = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing email address in Planning Center People.

    Args:
        email_id (str): The ID of the email to update.
        address (str, optional): The new email address.
        location (str, optional): The new location label.
        primary (bool, optional): Whether this should be the primary email.

    Returns:
        dict: The updated email data.
    """
    body = _build_patch_body("Email", address=address, location=location, primary=primary)
    response = await asyncio.to_thread(pco.patch, f"/people/v2/emails/{email_id}", body)
    return response["data"]


@mcp.tool()
async def delete_email(email_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete an email address from Planning Center People.

    Args:
        email_id (str): The ID of the email to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/people/v2/emails/{email_id}")
    return {"success": True, "message": f"Email {email_id} deleted successfully."}


# =============================================================================
# Phone Number Operations
# =============================================================================

@mcp.tool()
async def get_person_phone_numbers(person_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of phone numbers for a specific person.

    Args:
        person_id (str): The ID of the person.

    Returns:
        list: A list of phone number data.
    """
    response = await asyncio.to_thread(pco.get, f"/people/v2/people/{person_id}/phone_numbers")
    return response["data"]


@mcp.tool()
async def create_person_phone_number(
    person_id: str,
    number: str,
    location: str = "Mobile",
    primary: bool = False,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Add a phone number to a person in Planning Center People.

    Args:
        person_id (str): The ID of the person.
        number (str): The phone number.
        location (str, optional): Location label (e.g., "Mobile", "Home", "Work"). Default: "Mobile".
        primary (bool, optional): Whether this is the primary phone number. Default: False.

    Returns:
        dict: The created phone number data.
    """
    body = pco.template("PhoneNumber", {"number": number, "location": location, "primary": primary})
    response = await asyncio.to_thread(pco.post, f"/people/v2/people/{person_id}/phone_numbers", body)
    return response["data"]


@mcp.tool()
async def update_phone_number(
    phone_number_id: str,
    number: str = None,
    location: str = None,
    primary: bool = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing phone number in Planning Center People.

    Args:
        phone_number_id (str): The ID of the phone number to update.
        number (str, optional): The new phone number.
        location (str, optional): The new location label.
        primary (bool, optional): Whether this should be the primary phone number.

    Returns:
        dict: The updated phone number data.
    """
    body = _build_patch_body("PhoneNumber", number=number, location=location, primary=primary)
    response = await asyncio.to_thread(pco.patch, f"/people/v2/phone_numbers/{phone_number_id}", body)
    return response["data"]


@mcp.tool()
async def delete_phone_number(phone_number_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a phone number from Planning Center People.

    Args:
        phone_number_id (str): The ID of the phone number to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/people/v2/phone_numbers/{phone_number_id}")
    return {"success": True, "message": f"Phone number {phone_number_id} deleted successfully."}


# =============================================================================
# Address Operations
# =============================================================================

@mcp.tool()
async def get_person_addresses(person_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of addresses for a specific person.

    Args:
        person_id (str): The ID of the person.

    Returns:
        list: A list of address data.
    """
    response = await asyncio.to_thread(pco.get, f"/people/v2/people/{person_id}/addresses")
    return response["data"]


@mcp.tool()
async def create_person_address(
    person_id: str,
    street: str,
    city: str,
    state: str,
    zip: str,
    location: str = "Home",
    primary: bool = False,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Add an address to a person in Planning Center People.

    Args:
        person_id (str): The ID of the person.
        street (str): Street address (line 1, optionally including line 2).
        city (str): City.
        state (str): State or province.
        zip (str): ZIP or postal code.
        location (str, optional): Location label (e.g., "Home", "Work"). Default: "Home".
        primary (bool, optional): Whether this is the primary address. Default: False.

    Returns:
        dict: The created address data.
    """
    body = pco.template("Address", {
        "street": street,
        "city": city,
        "state": state,
        "zip": zip,
        "location": location,
        "primary": primary,
    })
    response = await asyncio.to_thread(pco.post, f"/people/v2/people/{person_id}/addresses", body)
    return response["data"]


@mcp.tool()
async def update_address(
    address_id: str,
    street: str = None,
    city: str = None,
    state: str = None,
    zip: str = None,
    location: str = None,
    primary: bool = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing address in Planning Center People.

    Args:
        address_id (str): The ID of the address to update.
        street (str, optional): New street address.
        city (str, optional): New city.
        state (str, optional): New state.
        zip (str, optional): New ZIP code.
        location (str, optional): New location label.
        primary (bool, optional): Whether this should be the primary address.

    Returns:
        dict: The updated address data.
    """
    body = _build_patch_body(
        "Address",
        street=street,
        city=city,
        state=state,
        zip=zip,
        location=location,
        primary=primary,
    )
    response = await asyncio.to_thread(pco.patch, f"/people/v2/addresses/{address_id}", body)
    return response["data"]


# =============================================================================
# Household Operations
# =============================================================================

@mcp.tool()
async def get_households(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of households from Planning Center People.

    Returns:
        list: A list of household data.
    """
    response = await asyncio.to_thread(pco.get, "/people/v2/households?per_page=100&order=name")
    return response["data"]


@mcp.tool()
async def get_household(household_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific household.

    Args:
        household_id (str): The ID of the household.

    Returns:
        dict: The household data.
    """
    response = await asyncio.to_thread(pco.get, f"/people/v2/households/{household_id}")
    return response["data"]


@mcp.tool()
async def get_household_people(household_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch the people in a specific household.

    Args:
        household_id (str): The ID of the household.

    Returns:
        list: A list of person data for members of the household.
    """
    response = await asyncio.to_thread(pco.get, f"/people/v2/households/{household_id}/people")
    return response["data"]


@mcp.tool()
async def create_household(
    name: str,
    primary_contact_id: str,
    people_ids: list,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new household in Planning Center People.

    Args:
        name (str): The household name.
        primary_contact_id (str): The ID of the person who is the primary contact.
        people_ids (list[str]): A list of person IDs to add to the household.

    Returns:
        dict: The created household data.
    """
    body = {
        "data": {
            "type": "Household",
            "attributes": {"name": name},
            "relationships": {
                "primary_contact": {
                    "data": {"type": "Person", "id": primary_contact_id}
                },
                "people": {
                    "data": [{"type": "Person", "id": pid} for pid in people_ids]
                },
            },
        }
    }
    response = await asyncio.to_thread(pco.post, "/people/v2/households", body)
    return response["data"]


@mcp.tool()
async def update_household(
    household_id: str,
    name: str = None,
    primary_contact_id: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing household in Planning Center People.

    Args:
        household_id (str): The ID of the household to update.
        name (str, optional): The new household name.
        primary_contact_id (str, optional): The ID of the new primary contact.

    Returns:
        dict: The updated household data.
    """
    data: dict = {"type": "Household", "attributes": {}, "relationships": {}}
    if name is not None:
        data["attributes"]["name"] = name
    if primary_contact_id is not None:
        data["relationships"]["primary_contact"] = {
            "data": {"type": "Person", "id": primary_contact_id}
        }
    response = await asyncio.to_thread(
        pco.patch, f"/people/v2/households/{household_id}", {"data": data}
    )
    return response["data"]


# =============================================================================
# List Operations
# =============================================================================

@mcp.tool()
async def get_lists(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch all lists (segments) from Planning Center People.

    Lists are saved queries used to group people based on shared criteria.

    Returns:
        list: A list of list data.
    """
    response = await asyncio.to_thread(pco.get, "/people/v2/lists?per_page=100&order=name")
    return response["data"]


@mcp.tool()
async def get_list(list_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific list.

    Args:
        list_id (str): The ID of the list.

    Returns:
        dict: The list data.
    """
    response = await asyncio.to_thread(pco.get, f"/people/v2/lists/{list_id}")
    return response["data"]


@mcp.tool()
async def get_list_people(list_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch the people in a specific list.

    Args:
        list_id (str): The ID of the list.

    Returns:
        list: A list of person data for members of the list.
    """
    response = await asyncio.to_thread(
        pco.get, f"/people/v2/lists/{list_id}/people?per_page=100"
    )
    return response["data"]


# =============================================================================
# Note Operations
# =============================================================================

@mcp.tool()
async def get_person_notes(person_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch notes for a specific person.

    Args:
        person_id (str): The ID of the person.

    Returns:
        list: A list of note data.
    """
    response = await asyncio.to_thread(
        pco.get, f"/people/v2/people/{person_id}/notes?order=-created_at"
    )
    return response["data"]


@mcp.tool()
async def create_person_note(
    person_id: str,
    note: str,
    note_category_id: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a note for a person in Planning Center People.

    Args:
        person_id (str): The ID of the person.
        note (str): The note content.
        note_category_id (str, optional): The ID of the note category.

    Returns:
        dict: The created note data.
    """
    attributes = {"note": note}
    relationships = {}
    if note_category_id is not None:
        relationships["note_category"] = {
            "data": {"type": "NoteCategory", "id": note_category_id}
        }

    body: dict = {"data": {"type": "Note", "attributes": attributes}}
    if relationships:
        body["data"]["relationships"] = relationships

    response = await asyncio.to_thread(pco.post, f"/people/v2/people/{person_id}/notes", body)
    return response["data"]


# =============================================================================
# Campus Operations
# =============================================================================

@mcp.tool()
async def get_campuses(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of campuses from Planning Center People.

    Returns:
        list: A list of campus data.
    """
    response = await asyncio.to_thread(pco.get, "/people/v2/campuses")
    return response["data"]


@mcp.tool()
async def get_campus(campus_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific campus.

    Args:
        campus_id (str): The ID of the campus.

    Returns:
        dict: The campus data.
    """
    response = await asyncio.to_thread(pco.get, f"/people/v2/campuses/{campus_id}")
    return response["data"]


# =============================================================================
# Field Definition & Custom Field Operations
# =============================================================================

@mcp.tool()
async def get_field_definitions(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch all custom field definitions from Planning Center People.

    Field definitions describe the custom fields available for people records.
    Use the returned IDs with get_person_field_data and create_person_field_datum.

    Returns:
        list: A list of field definition data.
    """
    response = await asyncio.to_thread(pco.get, "/people/v2/field_definitions")
    return response["data"]


@mcp.tool()
async def get_person_field_data(person_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch custom field values for a specific person.

    Args:
        person_id (str): The ID of the person.

    Returns:
        list: A list of field datum data, each containing a value and a reference
              to its field definition.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/people/v2/people/{person_id}/field_data?include=field_definition",
    )
    return response["data"]


@mcp.tool()
async def create_person_field_datum(
    person_id: str,
    field_definition_id: str,
    value: str,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Set a custom field value for a person in Planning Center People.

    Args:
        person_id (str): The ID of the person.
        field_definition_id (str): The ID of the field definition (from get_field_definitions).
        value (str): The value to set for this custom field.

    Returns:
        dict: The created field datum data.
    """
    body = {
        "data": {
            "type": "FieldDatum",
            "attributes": {"value": value},
            "relationships": {
                "field_definition": {
                    "data": {"type": "FieldDefinition", "id": field_definition_id}
                }
            },
        }
    }
    response = await asyncio.to_thread(pco.post, f"/people/v2/people/{person_id}/field_data", body)
    return response["data"]


@mcp.tool()
async def update_person_field_datum(
    field_datum_id: str,
    value: str,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update a custom field value for a person in Planning Center People.

    Args:
        field_datum_id (str): The ID of the field datum to update.
        value (str): The new value.

    Returns:
        dict: The updated field datum data.
    """
    body = _build_patch_body("FieldDatum", value=value)
    response = await asyncio.to_thread(pco.patch, f"/people/v2/field_data/{field_datum_id}", body)
    return response["data"]


@mcp.tool()
async def delete_person_field_datum(field_datum_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a custom field value from Planning Center People.

    Args:
        field_datum_id (str): The ID of the field datum to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/people/v2/field_data/{field_datum_id}")
    return {"success": True, "message": f"Field datum {field_datum_id} deleted successfully."}
