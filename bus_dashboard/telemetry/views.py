import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import BusTelemetry

# Endpoint 1: Receives data from your Python OpenCV script
@csrf_exempt
def update_telemetry(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            BusTelemetry.objects.create(
                boarding_count=data.get('boarding', 0),
                deboarding_count=data.get('deboarding', 0),
                passengers_inside=data.get('inside', 0),
                available_seats=data.get('available', 0),
                is_bus_full=data.get('is_full', False)
            )
            return JsonResponse({"status": "success", "message": "Telemetry logged."})
        except Exception as e:
            # THIS WILL PRINT THE EXACT ERROR IN YOUR TERMINAL
            print("\n=========================================")
            print(f"🚨 DATABASE ERROR: {e}")
            print("=========================================\n")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
            
    return JsonResponse({"status": "invalid request"}, status=405)

# Endpoint 2: Sends the latest data to your React dashboard
def get_latest_telemetry(request):
    latest_log = BusTelemetry.objects.order_by('-timestamp').first()
    if latest_log:
        return JsonResponse({
            "boarding": latest_log.boarding_count,
            "deboarding": latest_log.deboarding_count,
            "inside": latest_log.passengers_inside,
            "available": latest_log.available_seats,
            "is_full": latest_log.is_bus_full
        })
    return JsonResponse({"error": "No data available yet"}, status=404)