# from flask import Flask, jsonify, request
# from database import db, LocationHistory, HistoricalPlace
# from writer import load_qwen_model, write_history, extract_historical_places

# # -------------------------------------------------------
# # Flask App Setup
# # -------------------------------------------------------
# app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///locations.db"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# db.init_app(app)

# # Load model globally (once)
# model, tokenizer = load_qwen_model()


# # -------------------------------------------------------
# # 🕰️ API 1: Get or Generate Location History
# # -------------------------------------------------------
# @app.route("/api/history/<string:location>", methods=["GET"])
# def get_location_history(location):
#     try:
#         existing = LocationHistory.query.filter(
#             LocationHistory.place_name.ilike(location)
#         ).first()

#         if existing and existing.description:
#             return jsonify({
#                 "source": "database",
#                 "location": existing.place_name,
#                 "history": existing.description
#             }), 200

#         result = write_history(model, tokenizer, location)
#         if "error" in result:
#             return jsonify(result), 500

#         new_entry = LocationHistory(
#             place_name=location,
#             description=result["history"]
#         )
#         db.session.add(new_entry)
#         db.session.commit()

#         return jsonify({
#             "source": "model",
#             "location": location,
#             "history": result["history"]
#         }), 201

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

# @app.route("/api/historical_places/<string:location>", methods=["GET"])
# def get_historical_places(location):
#     try:
#         # ✅ Check if already exists in DB
#         loc_entry = LocationHistory.query.filter(
#             LocationHistory.place_name.ilike(location)
#         ).first()

#         if loc_entry and loc_entry.historical_places:
#             places_data = [
#                 {"name": p.name, "description": p.description}
#                 for p in loc_entry.historical_places
#             ]
#             return jsonify({
#                 "source": "database",
#                 "location": location,
#                 "historical_places": places_data
#             }), 200

#         result = extract_historical_places(model, tokenizer, location)
#         if "error" in result:
#             return jsonify(result), 500

#         places_list = result.get("locations", [])
#         if not places_list:
#             return jsonify({"message": "No historical places found."}), 404

#         if not loc_entry:
#             loc_entry = LocationHistory(place_name=location)
#             db.session.add(loc_entry)
#             db.session.commit()

#         for name in places_list:
#             new_place = HistoricalPlace(
#                 location_id=loc_entry.id,
#                 name=name,
#                 description=f"One of the historical sites near {location}."
#             )
#             db.session.add(new_place)
#         db.session.commit()

#         return jsonify({
#             "source": "model",
#             "location": location,
#             "historical_places": places_list
#         }), 201

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

# if __name__ == "__main__":
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)


import os
import logging
from flask import Flask, jsonify, request
from flask_caching import Cache
from flask_cors import CORS
from database import db, LocationHistory, HistoricalPlace
from writer import load_qwen_model, write_history, extract_historical_places


# -------------------------------------------------------
# 🔧 Flask App Configuration
# -------------------------------------------------------
def create_app():
    app = Flask(__name__)

    # ✅ Configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///locations.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CACHE_TYPE"] = "SimpleCache"  # You can switch to RedisCache for scale
    app.config["CACHE_DEFAULT_TIMEOUT"] = 3600  # 1 hour cache

    db.init_app(app)
    cache = Cache(app)
    CORS(app)  # Allow cross-origin for frontend access

    # ✅ Structured logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler(),
        ],
    )

    logger = logging.getLogger(__name__)

    # ✅ Load model once globally
    try:
        logger.info("Loading Qwen model...")
        model, tokenizer = load_qwen_model()
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        model, tokenizer = None, None

    # -------------------------------------------------------
    # 🕰️ API 1: Get or Generate Location History
    # -------------------------------------------------------
    @app.route("/api/history/<string:location>", methods=["GET"])
    @cache.cached()  # 🔥 Cache the endpoint
    def get_location_history(location):
        try:
            logger.info(f"Request received for history: {location}")
            existing = LocationHistory.query.filter(
                LocationHistory.place_name.ilike(location)
            ).first()

            if existing and existing.description:
                logger.info(f"Cache hit for location: {location}")
                return jsonify({
                    "source": "database",
                    "location": existing.place_name,
                    "history": existing.description
                }), 200

            if not model or not tokenizer:
                return jsonify({"error": "Model not loaded"}), 500

            result = write_history(model, tokenizer, location)
            if "error" in result:
                return jsonify(result), 500

            new_entry = LocationHistory(
                place_name=location,
                description=result["history"]
            )
            db.session.add(new_entry)
            db.session.commit()

            return jsonify({
                "source": "model",
                "location": location,
                "history": result["history"]
            }), 201

        except Exception as e:
            db.session.rollback()
            logger.exception("Error in get_location_history")
            return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

    # -------------------------------------------------------
    # 🏛️ API 2: Get or Generate Historical Places
    # -------------------------------------------------------
    @app.route("/api/historical_places/<string:location>", methods=["GET"])
    @cache.cached()
    def get_historical_places(location):
        try:
            logger.info(f"Request received for historical places: {location}")
            loc_entry = LocationHistory.query.filter(
                LocationHistory.place_name.ilike(location)
            ).first()

            if loc_entry and loc_entry.historical_places:
                places_data = [
                    {"name": p.name, "description": p.description}
                    for p in loc_entry.historical_places
                ]
                logger.info(f"Found cached historical places for: {location}")
                return jsonify({
                    "source": "database",
                    "location": location,
                    "historical_places": places_data
                }), 200

            if not model or not tokenizer:
                return jsonify({"error": "Model not loaded"}), 500

            result = extract_historical_places(model, tokenizer, location)
            if "error" in result:
                return jsonify(result), 500

            places_list = result.get("locations", [])
            if not places_list:
                return jsonify({"message": "No historical places found."}), 404

            if not loc_entry:
                loc_entry = LocationHistory(place_name=location)
                db.session.add(loc_entry)
                db.session.commit()

            for name in places_list:
                new_place = HistoricalPlace(
                    location_id=loc_entry.id,
                    name=name,
                    description=f"One of the historical sites near {location}."
                )
                db.session.add(new_place)
            db.session.commit()

            return jsonify({
                "source": "model",
                "location": location,
                "historical_places": places_list
            }), 201

        except Exception as e:
            db.session.rollback()
            logger.exception("Error in get_historical_places")
            return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

    # -------------------------------------------------------
    # Health Check Endpoint
    # -------------------------------------------------------
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"}), 200

    # -------------------------------------------------------
    # Initialize Database
    # -------------------------------------------------------
    with app.app_context():
        db.create_all()

    return app


# -------------------------------------------------------
# Run with Gunicorn (Production)
# -------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
