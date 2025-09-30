from flask import Blueprint, jsonify, request
bp = Blueprint("billing", __name__, url_prefix="/api/billing")

@bp.get("/plans")
def plans():
    return jsonify({
        "plans": [
            {"id":"starter","name":"Starter","price":0,"currency":"USD","interval":"month"},
            {"id":"pro","name":"Pro","price":29,"currency":"USD","interval":"month"},
            {"id":"enterprise","name":"Enterprise","price":99,"currency":"USD","interval":"month"}
        ]
    })

@bp.post("/checkout/session")
def checkout_session():
    payload = request.get_json(silent=True) or {}
    plan = payload.get("plan_id","starter")
    # TODO: Stripe Session 之後接入；先回 mock
    return jsonify({
        "session_id":"cs_test_mock_123",
        "plan_id": plan,
        "status":"created",
        "redirect_url":"https://example.com/checkout/success?session_id=cs_test_mock_123"
    }), 201
