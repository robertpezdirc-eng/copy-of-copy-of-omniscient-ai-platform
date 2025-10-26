{
  "displayName": "Cloud Run Availability (low traffic heuristic) - ${SERVICE_NAME}",
  "userLabels": {
    "service": "${SERVICE_NAME}",
    "env": "prod"
  },
  "conditions": [
    {
      "displayName": "No requests for ${WINDOW_MIN}m",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.label.\"service_name\"=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\"",
        "aggregations": [
          {
            "alignmentPeriod": "${ALIGNMENT_SEC}s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_SUM",
            "groupByFields": [
              "resource.label.\"service_name\""
            ]
          }
        ],
        "comparison": "COMPARISON_LT",
        "thresholdValue": 0.1,
        "duration": "${WINDOW_MIN}m",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "documentation": {
    "content": "Heuristic for low-traffic services: alert if the service receives no requests for a sustained period. Consider adding an Uptime Check and an HTTP health endpoint.",
    "mimeType": "text/markdown"
  },
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [ ${NOTIFICATION_CHANNELS} ]
}