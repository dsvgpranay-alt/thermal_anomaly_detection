from flask import Flask, request, jsonify
from model import *
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///thermal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

@app.route("/assets",methods=["POST"])
def assets():
    data=request.get_json()
    assets=Asset(asset_id=data["asset_id"],name=data["name"],type=data["type"],location=data["location"],warning_limit_C=data["warning_limit_C"],critical_limit_C=data["critical_limit_C"])
    db.session.add(assets)
    db.session.commit()
    return jsonify({"message": "Asset created successfully"}),201

@app.route("/assets", methods=["GET"])
def get_assets():
    assets=Asset.query.all()
    result=[]
    for asset in assets:
        result.append({"asset_id": asset.asset_id,"name": asset.name,"type": asset.type,"location": asset.location,"warning_limit_C": asset.warning_limit_C,"critical_limit_C": asset.critical_limit_C})
    return jsonify(result), 200

@app.route("/inspections", methods=["POST"])
def inspections():
    data = request.get_json()
    idempotency_key = data.get("idempotency_key")
    if not idempotency_key:
        return jsonify({"error": "Idempotency key is required"}), 400
    existing = Inspection.query.filter_by(idempotency_key=idempotency_key).first()
    if existing:
        return jsonify({"message": "Inspection already exists","inspection_id": existing.id}),200
    asset = Asset.query.filter_by(asset_id=data["asset_id"]).first()
    if not asset:
        return jsonify({"error": "Asset Not Found"}), 404
    inspection = Inspection(asset_id=data["asset_id"],timestamp=datetime.now(timezone.utc),max_temp_C=data["max_temp_C"],mean_temp_C=data["mean_temp_C"],idempotency_key=idempotency_key)
    db.session.add(inspection)
    db.session.flush()
    alert = None
    if inspection.max_temp_C >= asset.critical_limit_C:
        alert = Alert(inspection_id=inspection.id, severity="critical", status="open")
    elif inspection.max_temp_C >= asset.warning_limit_C:
        alert = Alert(inspection_id=inspection.id, severity="warning", status="open")
    if alert:
        db.session.add(alert)
    db.session.commit()
    return jsonify({"message": "Inspection created successfully","inspection_id": inspection.id,"alert": {"severity": alert.severity,"status": alert.status} if alert else None}), 201

@app.route("/assets/<int:asset_id>/inspections",methods=["GET"])
def inspection_list(asset_id):
    inspection=Inspection.query.filter_by(asset_id=asset_id).order_by(Inspection.timestamp.desc()).all()
    if not inspection:
        return jsonify({"message":"No Inspection Found For Asset"}),404
    result=[]
    for row in inspection:
        result.append({"id":row.id,"asset_id":row.asset_id,"max_temp_C":row.max_temp_C,"mean_temp_C":row.mean_temp_C,"timestamp":row.timestamp.isoformat()})
    
    return jsonify(result),200

@app.route("/alerts",methods=["GET"])
def alerts():
    alerts=Alert.query.filter_by(status="open").all()
    result=[]
    for row in alerts:
        result.append({"id":row.id,"inspection_id":row.inspection_id,"severity":row.severity,"status":row.status})
    return jsonify(result), 200

@app.route("/assets/<int:asset_id>", methods=["PATCH"])
def update_assets(asset_id):
    asset=Asset.query.filter_by(asset_id=asset_id).first()
    data=request.get_json()
    if not asset:
        return {"error": "Asset not found"},404
    if "name" in data:
        asset.name=data["name"]
    if "location" in data:
        asset.location=data["location"]
    if "warning_limit_C" in data:
        asset.warning_limit_C=data["warning_limit_C"]
    if "critical_limit_C" in data:
        asset.critical_limit_C=data["critical_limit_C"]
    db.session.commit()
    return {"message": "Asset updated successfully"}, 200

@app.route("/alerts/<int:alert_id>/acknowledge", methods=["PATCH"])
def acknowledge_alert(alert_id):
    data=request.get_json()
    alert=Alert.query.filter_by(id=alert_id).first()
    if not alert:
        return jsonify({"error": "Alert Not Found"}), 404
    if alert.status != "open":
        return jsonify({"error": "Alert is already acknowledged"}), 409
    if not data or not data.get("acknowledged_by"):
        return jsonify({"error": "Acknowledged by is required"}), 400
    previous_status=alert.status
    current_time=datetime.now(timezone.utc)
    alert.status = "acknowledged"
    alert.acknowledged_by = data["acknowledged_by"]
    alert.acknowledged_at = current_time
    history = AlertAcknowledgement(alert_id=alert.id,previous_status=previous_status,new_status="acknowledged",acknowledged_by=data["acknowledged_by"],acknowledged_at=current_time)
    db.session.add(history)
    db.session.commit()
    return jsonify({"message": "Alert acknowledged successfully","alert_id": alert.id,"previous_status": previous_status,"new_status": alert.status,"acknowledged_by": alert.acknowledged_by,"acknowledged_at": alert.acknowledged_at.isoformat()}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)