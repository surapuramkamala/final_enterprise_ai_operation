
from uuid import uuid4

pending_approvals = {}


def create_change_request(action: str, user_id: str) -> dict:
    request_id = str(uuid4())

    pending_approvals[request_id] = {
        "action": action,
        "user_id": user_id,
        "status": "pending",
    }

    return {
        "request_id": request_id,
        "status": "pending_approval",
        "message": "Waiting for an authorized approver.",
    }


def approve_change(
    request_id: str,
    approver_id: str,
) -> dict:
    request = pending_approvals.get(request_id)

    if request is None:
        return {"error": "Request not found"}

    if request["status"] != "pending":
        return {"error": "Request is not pending"}

    if request["user_id"] == approver_id:
        return {"error": "Requester cannot approve their own request"}

    request["status"] = "approved"
    request["approved_by"] = approver_id

    # No real production operation is executed here.
    return {
        "request_id": request_id,
        "status": "approved",
        "message": "Approval recorded; no external action executed.",
    }
