{
  "displayName": "Cloud Run 5xx Error Rate - ${SERVICE_NAME}",
  "userLabels": {
    "service": "${SERVICE_NAME}",
    "env": "prod"
  },
  "conditions": [
    {
      "displayName": "5xx errors > ${ERRORS_THRESHOLD} in ${WINDOW_MIN}m",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.label.\"service_name\"=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.label.\"response_code_class\"=\"5xx\"",
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
        "comparison": "COMPARISON_GT",
        "thresholdValue": ${ERRORS_THRESHOLD},
        "duration": "${WINDOW_MIN}m",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [ ${NOTIFICATION_CHANNELS} ]
}