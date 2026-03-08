import asyncio

from uncalled_for import Depends
from pypco import PCO

from server import mcp, get_pco, _build_patch_body


# =============================================================================
# Fund Operations
# =============================================================================

@mcp.tool()
async def get_funds(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of funds from Planning Center Giving.

    Funds are buckets that donors can put money into and that churches use
    to organize incoming gifts and set budgets.

    Returns:
        list: A list of fund data.
    """
    response = await asyncio.to_thread(pco.get, "/giving/v2/funds")
    return response["data"]

@mcp.tool()
async def get_fund(fund_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific fund.

    Args:
        fund_id (str): The ID of the fund.

    Returns:
        dict: The fund data.
    """
    response = await asyncio.to_thread(pco.get, f"/giving/v2/funds/{fund_id}")
    return response["data"]

@mcp.tool()
async def create_fund(
    name: str,
    description: str = None,
    ledger_code: str = None,
    default: bool = None,
    visibility: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new fund in Planning Center Giving.

    Args:
        name (str): The name of the fund.
        description (str, optional): A description of the fund.
        ledger_code (str, optional): The ledger code for accounting.
        default (bool, optional): Whether this is the default fund.
        visibility (str, optional): Fund visibility (e.g., "hidden", "everywhere").

    Returns:
        dict: The created fund data.
    """
    attributes = {"name": name}
    if description is not None:
        attributes["description"] = description
    if ledger_code is not None:
        attributes["ledger_code"] = ledger_code
    if default is not None:
        attributes["default"] = default
    if visibility is not None:
        attributes["visibility"] = visibility

    body = pco.template("Fund", attributes)
    response = await asyncio.to_thread(pco.post, "/giving/v2/funds", body)
    return response["data"]

@mcp.tool()
async def update_fund(
    fund_id: str,
    name: str = None,
    description: str = None,
    ledger_code: str = None,
    default: bool = None,
    visibility: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing fund in Planning Center Giving.

    Args:
        fund_id (str): The ID of the fund to update.
        name (str, optional): The new name for the fund.
        description (str, optional): The new description.
        ledger_code (str, optional): The new ledger code.
        default (bool, optional): Whether this is the default fund.
        visibility (str, optional): The new visibility setting.

    Returns:
        dict: The updated fund data.
    """
    body = _build_patch_body(
        "Fund",
        name=name,
        description=description,
        ledger_code=ledger_code,
        default=default,
        visibility=visibility,
    )
    response = await asyncio.to_thread(pco.patch, f"/giving/v2/funds/{fund_id}", body)
    return response["data"]

@mcp.tool()
async def delete_fund(fund_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a fund from Planning Center Giving.

    Args:
        fund_id (str): The ID of the fund to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/giving/v2/funds/{fund_id}")
    return {"success": True, "message": f"Fund {fund_id} deleted successfully."}


# =============================================================================
# Batch Operations
# =============================================================================

@mcp.tool()
async def get_batches(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of donation batches from Planning Center Giving.

    A batch is a grouping of donations.

    Returns:
        list: A list of batch data.
    """
    response = await asyncio.to_thread(pco.get, "/giving/v2/batches?order=-created_at")
    return response["data"]

@mcp.tool()
async def get_batch(batch_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific batch.

    Args:
        batch_id (str): The ID of the batch.

    Returns:
        dict: The batch data.
    """
    response = await asyncio.to_thread(pco.get, f"/giving/v2/batches/{batch_id}")
    return response["data"]

@mcp.tool()
async def create_batch(
    description: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new donation batch in Planning Center Giving.

    Args:
        description (str, optional): A description for the batch.

    Returns:
        dict: The created batch data.
    """
    attributes = {}
    if description is not None:
        attributes["description"] = description

    body = pco.template("Batch", attributes)
    response = await asyncio.to_thread(pco.post, "/giving/v2/batches", body)
    return response["data"]

@mcp.tool()
async def update_batch(
    batch_id: str,
    description: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing batch in Planning Center Giving.

    Args:
        batch_id (str): The ID of the batch to update.
        description (str, optional): The new description.

    Returns:
        dict: The updated batch data.
    """
    body = _build_patch_body("Batch", description=description)
    response = await asyncio.to_thread(pco.patch, f"/giving/v2/batches/{batch_id}", body)
    return response["data"]

@mcp.tool()
async def commit_batch(batch_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Commit a batch in Planning Center Giving, finalizing its donations.

    Args:
        batch_id (str): The ID of the batch to commit.

    Returns:
        dict: A confirmation message.
    """
    body = _build_patch_body("Batch", status="committed")
    response = await asyncio.to_thread(pco.patch, f"/giving/v2/batches/{batch_id}", body)
    return response["data"]

@mcp.tool()
async def delete_batch(batch_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a batch from Planning Center Giving.

    Args:
        batch_id (str): The ID of the batch to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/giving/v2/batches/{batch_id}")
    return {"success": True, "message": f"Batch {batch_id} deleted successfully."}


# =============================================================================
# Donation Operations
# =============================================================================

@mcp.tool()
async def get_donations(batch_id: str = None, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of donations from Planning Center Giving.

    Args:
        batch_id (str, optional): If provided, only return donations in this batch.

    Returns:
        list: A list of donation data.
    """
    if batch_id:
        path = f"/giving/v2/batches/{batch_id}/donations?include=designations"
    else:
        path = "/giving/v2/donations?include=designations&order=-created_at"
    response = await asyncio.to_thread(pco.get, path)
    return response["data"]

@mcp.tool()
async def get_donation(donation_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific donation, including its designations.

    Args:
        donation_id (str): The ID of the donation.

    Returns:
        dict: The donation data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/giving/v2/donations/{donation_id}?include=designations"
    )
    return response["data"]

@mcp.tool()
async def create_donation(
    batch_id: str,
    payment_method: str,
    received_at: str,
    person_id: str,
    payment_source_id: str,
    fund_id: str,
    amount_cents: int,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Create a new donation in Planning Center Giving.

    Every donation must belong to a batch, be associated with a payment source,
    and have at least one designation linking an amount to a fund.

    Args:
        batch_id (str): The ID of the batch to add the donation to.
        payment_method (str): The payment method (e.g., "cash", "check", "card", "ach").
        received_at (str): When the donation was received in ISO 8601 format.
        person_id (str): The ID of the person (donor).
        payment_source_id (str): The ID of the payment source.
        fund_id (str): The ID of the fund to designate the donation to.
        amount_cents (int): The donation amount in cents (e.g., 5000 for $50.00).

    Returns:
        dict: The created donation data.
    """
    body = {
        "data": {
            "type": "Donation",
            "attributes": {
                "payment_method": payment_method,
                "received_at": received_at,
            },
            "relationships": {
                "person": {
                    "data": {"type": "Person", "id": person_id}
                },
                "payment_source": {
                    "data": {"type": "PaymentSource", "id": payment_source_id}
                },
            },
        },
        "included": [
            {
                "type": "Designation",
                "attributes": {
                    "amount_cents": amount_cents,
                },
                "relationships": {
                    "fund": {
                        "data": {"type": "Fund", "id": fund_id}
                    },
                },
            }
        ],
    }

    response = await asyncio.to_thread(
        pco.post,
        f"/giving/v2/batches/{batch_id}/donations",
        body,
    )
    return response["data"]

@mcp.tool()
async def update_donation(
    donation_id: str,
    payment_method: str = None,
    received_at: str = None,
    pco: PCO = Depends(get_pco),
) -> dict:
    """
    Update an existing donation in Planning Center Giving.

    Args:
        donation_id (str): The ID of the donation to update.
        payment_method (str, optional): The new payment method.
        received_at (str, optional): The new received date in ISO 8601 format.

    Returns:
        dict: The updated donation data.
    """
    body = _build_patch_body(
        "Donation",
        payment_method=payment_method,
        received_at=received_at,
    )
    response = await asyncio.to_thread(pco.patch, f"/giving/v2/donations/{donation_id}", body)
    return response["data"]

@mcp.tool()
async def delete_donation(donation_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Delete a donation from Planning Center Giving.

    Args:
        donation_id (str): The ID of the donation to delete.

    Returns:
        dict: A confirmation message.
    """
    await asyncio.to_thread(pco.delete, f"/giving/v2/donations/{donation_id}")
    return {"success": True, "message": f"Donation {donation_id} deleted successfully."}


# =============================================================================
# Designation Operations
# =============================================================================

@mcp.tool()
async def get_donation_designations(donation_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch the designations for a specific donation.

    A designation specifies how much of a donation goes to a given fund.

    Args:
        donation_id (str): The ID of the donation.

    Returns:
        list: A list of designation data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/giving/v2/donations/{donation_id}/designations"
    )
    return response["data"]


# =============================================================================
# Payment Source Operations
# =============================================================================

@mcp.tool()
async def get_payment_sources(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of payment sources from Planning Center Giving.

    A payment source represents the system that originally accepted a donation
    (e.g., your app, a kiosk, or a third-party integration).

    Returns:
        list: A list of payment source data.
    """
    response = await asyncio.to_thread(pco.get, "/giving/v2/payment_sources")
    return response["data"]

@mcp.tool()
async def get_payment_source(payment_source_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch details for a specific payment source.

    Args:
        payment_source_id (str): The ID of the payment source.

    Returns:
        dict: The payment source data.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/giving/v2/payment_sources/{payment_source_id}"
    )
    return response["data"]


# =============================================================================
# Donor Operations
# =============================================================================

@mcp.tool()
async def get_donors(pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch a list of donors from Planning Center Giving.

    Returns:
        list: A list of donor/people data with giving information.
    """
    response = await asyncio.to_thread(pco.get, "/giving/v2/people?per_page=100")
    return response["data"]

@mcp.tool()
async def get_donor(person_id: str, pco: PCO = Depends(get_pco)) -> dict:
    """
    Fetch giving details for a specific person/donor.

    Args:
        person_id (str): The ID of the person.

    Returns:
        dict: The donor data including giving totals.
    """
    response = await asyncio.to_thread(pco.get, f"/giving/v2/people/{person_id}")
    return response["data"]

@mcp.tool()
async def get_donor_donations(person_id: str, pco: PCO = Depends(get_pco)) -> list:
    """
    Fetch all donations made by a specific person.

    Args:
        person_id (str): The ID of the person.

    Returns:
        list: A list of donation data for this person.
    """
    response = await asyncio.to_thread(
        pco.get,
        f"/giving/v2/people/{person_id}/donations?include=designations&order=-created_at"
    )
    return response["data"]
