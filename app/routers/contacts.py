from fastapi import APIRouter

from app import store
from app.schemas import OptOutRequest

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.post("/opt-out")
def opt_out(body: OptOutRequest):
    """No contact records are stored, so opt-out just takes the phone
    number directly and adds it to the in-memory DNC set."""
    store.add_to_dnc(body.phone)
    return {"phone": body.phone, "suppressed": True}