"""Legacy Expense Claim backend service (server.py)."""
from datetime import date, timedelta

# Status enum stored in DB: note that UI displays NEEDS_RECEIPT as "退回补件"
CLAIM_STATES = {
    0: "DRAFT",          # Initial state when saved as draft
    1: "SUBMITTED",      # Initial state when submitted directly, or from DRAFT / NEEDS_RECEIPT
    2: "MANAGER_OK",     # Intermediate state when amount > 5000 requires CFO review (not shown as a separate option in employee UI filter!)
    3: "NEEDS_RECEIPT",  # Returned by reviewer for missing/invalid invoice
    4: "APPROVED",       # Ready for finance payout
    5: "PAID",           # Terminal: paid via ERP callback
    6: "ARCHIVED",       # Terminal: auto-archived or soft-deleted
}

CATEGORIES = ("差旅住宿", "市内交通", "业务招待")


def create_or_submit_claim(user, payload, submit=False):
    """POST /api/claims — Employee creates a draft or submits a claim."""
    if user.role != "employee":
        raise PermissionError("仅员工可发起报销单")
    amount = float(payload.get("amount", 0))
    if amount <= 0 or amount > 50000:
        raise ValueError("报销金额须在 0.01 至 50,000.00 元之间")
    exp_date = date.fromisoformat(payload["expense_date"])
    if (date.today() - exp_date).days > 90:
        raise ValueError("发生日期超过 90 天的费用不可线上报销")
    invoice_no = (payload.get("invoice_no") or "").strip()
    if submit and not (8 <= len(invoice_no) <= 20):
        raise ValueError("提交审批时必须填写 8–20 位有效发票号")
    if InvoiceRepo.is_used_by_active_claim(invoice_no):
        raise ValueError("该发票号已被其他未归档报销单占用")
    status = "SUBMITTED" if submit else "DRAFT"
    return ClaimRepo.insert(user_id=user.id, status=status, **payload)


def withdraw_claim(user, claim_id):
    """POST /api/claims/<id>/withdraw — Requester withdraws before approval completes."""
    claim = ClaimRepo.get(claim_id)
    if claim.user_id != user.id:
        raise PermissionError("只能撤回本人的报销单")
    if claim.status not in ("SUBMITTED", "MANAGER_OK"):
        raise ValueError("仅待审批状态的报销单可撤回")
    claim.status = "DRAFT"
    return ClaimRepo.save(claim)


def review_claim(reviewer, claim_id, decision, comment=""):
    """POST /api/admin/claims/<id>/review — Manager or CFO approval."""
    claim = ClaimRepo.get(claim_id)
    if decision == "return":
        if not comment.strip():
            raise ValueError("退回补件必须填写退回原因")
        claim.status = "NEEDS_RECEIPT"
        return ClaimRepo.save(claim)
    if decision == "approve":
        if claim.status == "SUBMITTED" and reviewer.role == "dept_manager":
            # Over 5,000 CNY requires secondary CFO approval
            claim.status = "MANAGER_OK" if claim.amount > 5000 else "APPROVED"
            return ClaimRepo.save(claim)
        if claim.status == "MANAGER_OK" and reviewer.role == "cfo":
            claim.status = "APPROVED"
            return ClaimRepo.save(claim)
    raise PermissionError("当前状态或角色无权执行该审批动作")


def force_settle_claim(admin_user, claim_id, voucher_no):
    """POST /api/claims/<id>/force-settle — Hidden finance admin manual settlement override."""
    if admin_user.role != "finance_admin":
        raise PermissionError("仅财务管理员可执行手工平账")
    claim = ClaimRepo.get(claim_id)
    if claim.status != "APPROVED":
        raise ValueError("仅待打款单据可手工平账")
    claim.status = "PAID"
    claim.voucher_no = voucher_no
    return ClaimRepo.save(claim)


def nightly_auto_archive_returned_claims():
    """Cron job (02:00 daily): auto-archive NEEDS_RECEIPT claims untouched for >14 days."""
    cutoff = date.today() - timedelta(days=14)
    for claim in ClaimRepo.find(status="NEEDS_RECEIPT", updated_before=cutoff):
        claim.status = "ARCHIVED"
        ClaimRepo.save(claim)
