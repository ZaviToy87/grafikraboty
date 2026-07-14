from flask import Blueprint, render_template, request, jsonify, send_file, current_app
import os
from werkzeug.utils import secure_filename
from ..analyzer import parse_sales_file, calculate_metrics, enrich_sales_data
from ..storage import LocalStorage

bp = Blueprint('sales', __name__, url_prefix='/sales')

# Хранилище
storage = LocalStorage(base_dir="uploads")

@bp.route('/analysis')
def sales_analysis():
    return render_template('sales_analysis.html')

@bp.route('/api/upload', methods=['POST'])
def upload_sales_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    # Сохраняем файл
    filename = secure_filename(file.filename)
    filepath = os.path.join(storage.base_dir, filename)
    file.save(filepath)

    try:
        sales = parse_sales_file(filepath, filename=filename)
        enriched = enrich_sales_data(sales)
        metrics = calculate_metrics(enriched)

        # Сохраняем в историю БД
        from ..storage import HistoryDB
        db = HistoryDB()
        period_id = db.save_period(filename, enriched)

        # Сохраняем результат в кэш (временно)
        result_id = storage.save_result(filename, {
            "sales": [s.dict() for s in enriched],
            "metrics": metrics,
            "filename": filename,
            "period_id": period_id
        })

        return jsonify({
            "success": True,
            "result_id": result_id,
            "period_id": period_id,
            "metrics": metrics,
            "total_sales": len(enriched)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/api/results/<result_id>')
def get_result(result_id):
    data = storage.load_result(result_id)
    if not data:
        return jsonify({"error": "Result not found"}), 404
    return jsonify(data)

@bp.route('/api/periods')
def list_periods():
    from ..storage import HistoryDB
    db = HistoryDB()
    periods = db.get_periods()
    return jsonify(periods)

@bp.route('/api/daily-summary')
def daily_summary():
    start = request.args.get('start')
    end = request.args.get('end')
    if not start or not end:
        return jsonify({"error": "Требуются параметры start и end в формате YYYY-MM-DD"}), 400
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError:
        return jsonify({"error": "Неверный формат даты"}), 400

    from ..storage import HistoryDB
    db = HistoryDB()
    summary = db.get_daily_summary(start_date, end_date)
    return jsonify(summary)

def init_sales_routes(app):
    app.register_blueprint(bp)