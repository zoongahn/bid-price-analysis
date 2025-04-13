import os
import subprocess
import json
import sys

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class PredictionViewSet(ViewSet):

    @action(detail=False, methods=["post"], url_path='run')
    def run_prediction(self, request):
        try:
            body = request.data
            notice_id = body.get("notice_id")

            python_path = sys.executable
            print(python_path)

            result = subprocess.run(
                [
                    "python",
                    "statsModelsPredict/src/run_load_and_predict.py",
                    "--notice_id", notice_id,
                ],
                capture_output=True,
                text=True,
                check=True
            )

            output = result.stdout.strip()
            prediction = json.loads(output)

            return Response(prediction, status=200)

        except subprocess.CalledProcessError as e:
            return Response({"error": "모델 실행 오류", "details": e.stderr}, status=500)
        except Exception as e:
            return Response({"error": str(e)}, status=500)